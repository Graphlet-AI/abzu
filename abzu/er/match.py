"""Entity resolution matching module using BAML async client."""

import asyncio
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast

import pandas as pd
from baml_py import Collector
from tqdm import tqdm

from abzu.baml_client import b as baml_client
from abzu.config import config
from abzu.er.uuid import process_block_with_uuid_mapping
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.utils import save_jsonl

logger = get_logger(__name__)

# Initialize collector for BAML tracking
collector = Collector()


async def process_block(
    block: dict[str, Any],
    semaphore: asyncio.Semaphore,
    iteration: int = 1,
) -> dict[str, Any]:
    """
    Process a single block of companies using MultiEntityResolution with UUID mapping.

    Args:
        block: Dictionary containing block data with companies list
        semaphore: Asyncio semaphore for rate limiting
        iteration: Current iteration number for match_skip_history tracking

    Returns:
        Dictionary with matched/resolved companies
    """
    async with semaphore:
        # Use the UUID mapping wrapper to process the block
        result: dict[str, Any] = await process_block_with_uuid_mapping(
            block=block,
            baml_client=baml_client,
            collector=collector,
            iteration=iteration,
        )

        # If the block was resolved, generate new UUIDs for the resolved companies
        if result.get("was_resolved") and "resolved_companies" in result:
            for company in result["resolved_companies"]:
                if "uuid" not in company or not company["uuid"]:
                    company["uuid"] = str(uuid.uuid4())
                    logger.debug(f"Generated new UUID for resolved company: {company['name']}")

        return result


async def process_blocks_async(
    blocks: list[dict[str, Any]],
    batch_size: int,
    iteration: int = 1,
) -> list[dict[str, Any]]:
    """
    Process all blocks concurrently with rate limiting.

    Args:
        blocks: List of block dictionaries
        batch_size: Maximum number of concurrent API calls
        iteration: Current iteration number for match_skip_history tracking

    Returns:
        List of resolved block dictionaries
    """
    semaphore = asyncio.Semaphore(batch_size)

    # Create tasks for all blocks
    tasks = [process_block(block, semaphore, iteration) for block in blocks]

    # Process with progress bar
    results = []
    with tqdm(total=len(tasks), desc="Processing blocks") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            pbar.update(1)

    return results


def backup_file(file_path: Path) -> None:
    """Create a backup of an existing file or directory, keeping only the most recent backup.

    Args:
        file_path: Path to the file or directory to backup
    """
    if file_path.exists():
        # Remove old backups first - keep only the most recent
        backup_pattern = f"{file_path.stem}_backup_*{file_path.suffix}"
        old_backups = sorted(file_path.parent.glob(backup_pattern))

        # Delete all old backups
        for old_backup in old_backups:
            if old_backup.exists():
                if old_backup.is_dir():
                    shutil.rmtree(old_backup)
                    logger.debug(f"Removed old backup directory: {old_backup}")
                else:
                    old_backup.unlink()
                    logger.debug(f"Removed old backup file: {old_backup}")

        # Create new backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"

        if file_path.is_dir():
            # Handle directory (e.g., PySpark parquet output)
            shutil.copytree(file_path, backup_path)
            logger.info(f"Created backup of directory: {backup_path}")
        else:
            # Handle single file
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of file: {backup_path}")


def match_entities(
    blocks_path: str = config.get("process.kg.er.paths.names.blocks"),
    output_path: str = config.get("process.kg.er.paths.names.matches"),
    iteration: int = 1,
    batch_size: int = 5,
    limit: Optional[int] = None,
    min_block_size: Optional[int] = None,
    max_block_size: Optional[int] = None,
) -> None:
    """
    Match entities within blocks using BAML MultiEntityResolution.

    Args:
        blocks_path: Path to the blocks parquet file (with {iteration} and {format} placeholders)
        output_path: Path to save the matched entities (with {iteration} and {format} placeholders)
        iteration: Iteration number for multi-round ER processing
        batch_size: Number of concurrent API calls
        limit: Maximum number of blocks to process (for testing)
        min_block_size: Minimum block size to process (inclusive)
        max_block_size: Maximum block size to process (inclusive)
    """
    # Format paths with iteration and format early for logging
    blocks_json_path = blocks_path.format(iteration=iteration, format="json")
    output_json_path = output_path.format(iteration=iteration, format="json")

    logger.info(f"Starting entity matching from {blocks_json_path}")
    logger.info(f"Output path: {output_json_path}")
    logger.info(f"Batch size: {batch_size}")
    if limit:
        logger.info(f"Limiting to {limit} blocks")
    if min_block_size is not None or max_block_size is not None:
        logger.info(f"Block size range: {min_block_size or 'any'}:{max_block_size or 'any'}")

    # Load blocks from JSON using PySpark to preserve Python lists

    # Create or get SparkSession
    spark = get_spark_session(f"EntityResolutionMatch_Iteration{iteration}")

    # Disable Arrow optimization to preserve Python object types
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

    # Load JSON file with Spark (preserves lists as Python lists, not numpy arrays)
    spark_df = spark.read.json(blocks_json_path)

    # Convert to pandas DataFrame
    # With Arrow disabled, toPandas() preserves Python lists without converting to numpy arrays
    df = spark_df.toPandas()

    # Convert any Row objects to dicts in the companies column
    from pyspark.sql.types import Row

    if "companies" in df.columns:

        def convert_row_to_dict(item: Any) -> Any:
            """Recursively convert Row objects to dicts."""
            if isinstance(item, Row):
                return item.asDict()
            elif isinstance(item, list):
                return [convert_row_to_dict(i) for i in item]
            elif isinstance(item, dict):
                return {k: convert_row_to_dict(v) for k, v in item.items()}
            else:
                return item

        df["companies"] = df["companies"].apply(convert_row_to_dict)

    logger.info(f"Loaded {len(df)} blocks")

    # Separate singleton blocks from multi-company blocks
    singleton_blocks = df[df["block_size"] == 1].copy()
    multi_company_blocks = df[df["block_size"] > 1].copy()
    logger.info(f"Found {len(singleton_blocks)} singleton blocks")
    logger.info(f"Found {len(multi_company_blocks)} blocks with multiple companies")

    # Apply size range filter if specified
    if min_block_size is not None:
        multi_company_blocks = multi_company_blocks[
            multi_company_blocks["block_size"] >= min_block_size
        ]
        logger.info(f"After min size filter ({min_block_size}): {len(multi_company_blocks)} blocks")

    if len(multi_company_blocks) == 0:
        logger.warning("No blocks found after filtering.")
        return

    if max_block_size is not None:
        multi_company_blocks = multi_company_blocks[
            multi_company_blocks["block_size"] <= max_block_size
        ]
        logger.info(f"After max size filter ({max_block_size}): {len(multi_company_blocks)} blocks")

    # Check if we have any blocks left after max size filter
    if len(multi_company_blocks) == 0 and len(singleton_blocks) == 0:
        logger.warning("No blocks found after applying filters.")
        return

    # Apply limit if specified
    if limit:
        multi_company_blocks = multi_company_blocks.head(limit)
        logger.info(f"Limited to {len(multi_company_blocks)} blocks")

    # Process multi-company blocks asynchronously if we have any
    if len(multi_company_blocks) > 0:
        # Convert to list of dictionaries for processing
        blocks = cast(list[dict[str, Any]], multi_company_blocks.to_dict("records"))

        # Process blocks asynchronously
        logger.info("Starting async processing...")
        results = asyncio.run(process_blocks_async(blocks, batch_size, iteration))
    else:
        logger.info("No multi-company blocks to process")
        results = []

    # Process error blocks BEFORE creating DataFrame
    error_recovery_count = 0
    for i, result in enumerate(results):
        # Check if this result has an error
        if "error" in result and result["error"] is not None:
            # Check if we have original_companies to recover
            if (
                "original_companies" in result
                and result["original_companies"] is not None
                and isinstance(result["original_companies"], list)
                and len(result["original_companies"]) > 0
            ):
                original_companies = result["original_companies"]

                # Mark these companies as error-recovered
                recovered_companies = []
                for company in original_companies:
                    # Make a copy to avoid modifying original
                    company_copy = dict(company) if isinstance(company, dict) else company

                    company_copy["match_skip"] = True
                    company_copy["match_skip_reason"] = "error_recovery"

                    # Update match_skip_history
                    skip_history_raw = company_copy.get("match_skip_history")
                    if skip_history_raw is None:
                        skip_history: list[int] = []
                    elif not isinstance(skip_history_raw, list):
                        # This should not happen with PySpark loading
                        logger.error(
                            f"Unexpected non-list type for match_skip_history: {type(skip_history_raw)}"
                        )
                        skip_history = []
                    else:
                        skip_history = skip_history_raw

                    if iteration not in skip_history:
                        skip_history.append(iteration)
                    company_copy["match_skip_history"] = skip_history

                    # Ensure source_uuids contains the company's UUID
                    if "uuid" in company_copy and company_copy["uuid"]:
                        source_uuids = company_copy.get("source_uuids")
                        if source_uuids is None:
                            source_uuids = [company_copy["uuid"]]
                        elif isinstance(source_uuids, list):
                            if company_copy["uuid"] not in source_uuids:
                                source_uuids.append(company_copy["uuid"])
                        else:
                            # This should not happen with PySpark loading
                            logger.error(
                                f"Unexpected non-list type for source_uuids: {type(source_uuids)}"
                            )
                            source_uuids = [company_copy["uuid"]]
                        company_copy["source_uuids"] = source_uuids

                    recovered_companies.append(company_copy)
                    error_recovery_count += 1

                # Update the result dictionary directly
                result["resolved_companies"] = recovered_companies
                result["was_resolved"] = False
                result["error_recovered"] = True

                logger.debug(
                    f"Recovered {len(recovered_companies)} companies from error block '{result.get('block_key', 'unknown')}'"
                )

    if error_recovery_count > 0:
        logger.info(f"Recovered {error_recovery_count} companies from error blocks")

    # Process singleton blocks (no matching needed, just pass through)
    singleton_results = []
    if len(singleton_blocks) > 0:
        logger.info(f"Processing {len(singleton_blocks)} singleton blocks...")
        for _, block in singleton_blocks.iterrows():
            block_dict = block.to_dict()
            companies = block_dict.get("companies", [])

            # For singleton blocks, the single company becomes the resolved company
            if companies and len(companies) > 0:
                company = companies[0]

                # Ensure the company has its own UUID in source_uuids
                if "uuid" in company and company["uuid"]:
                    source_uuids = company.get("source_uuids")
                    if source_uuids is None:
                        source_uuids = [company["uuid"]]
                    elif isinstance(source_uuids, list):
                        if company["uuid"] not in source_uuids:
                            source_uuids.append(company["uuid"])
                    else:
                        # This should not happen with PySpark loading
                        logger.error(
                            f"Unexpected non-list type for source_uuids in singleton: {type(source_uuids)}"
                        )
                        source_uuids = [company["uuid"]]
                    company["source_uuids"] = source_uuids

                # Mark as singleton (not processed by BAML)
                company["match_skip"] = True
                company["match_skip_reason"] = "singleton_block"

                # Initialize match_skip_history if not present
                skip_hist_raw = company.get("match_skip_history")
                if skip_hist_raw is None:
                    skip_hist: list[int] = []
                elif not isinstance(skip_hist_raw, list):
                    # This should not happen with PySpark loading
                    logger.error(
                        f"Unexpected non-list type for match_skip_history in singleton: {type(skip_hist_raw)}"
                    )
                    skip_hist = []
                else:
                    skip_hist = skip_hist_raw

                # Add current iteration to skip history
                if iteration not in skip_hist:
                    skip_hist.append(iteration)
                company["match_skip_history"] = skip_hist

                # Create result structure
                singleton_result = {
                    "block_key": block_dict.get("block_key"),
                    "block_key_type": block_dict.get("block_key_type"),
                    "original_companies": [company],
                    "resolved_companies": [company],
                    "original_count": 1,
                    "resolved_count": 1,
                    "was_resolved": False,  # No matching was done
                }
                singleton_results.append(singleton_result)

        logger.info(f"Processed {len(singleton_results)} singleton blocks")

    # Combine multi-company and singleton results
    all_results = results + singleton_results

    # Convert results to DataFrame
    results_df = pd.DataFrame(all_results)

    logger.info(
        f"Created DataFrame with {len(results_df)} rows and columns: {list(results_df.columns)}"
    )

    # Ensure required columns exist with default values
    if "resolved_companies" not in results_df.columns:
        results_df["resolved_companies"] = [[] for _ in range(len(results_df))]
    if "original_companies" not in results_df.columns:
        results_df["original_companies"] = [[] for _ in range(len(results_df))]

    # Debug: Check for mixed types before fixing
    if "resolved_companies" in results_df.columns:
        # Find any non-list values
        non_list_mask = ~results_df["resolved_companies"].apply(lambda x: isinstance(x, list))
        if non_list_mask.any():
            logger.warning(
                f"Found {non_list_mask.sum()} non-list values in resolved_companies column"
            )
            # Show sample of problematic values for debugging
            problematic = results_df[non_list_mask]["resolved_companies"].head(5)
            for idx, val in problematic.items():
                logger.debug(f"  Row {idx}: type={type(val)}, value={val}")

    # No longer need ensure_list workaround - PySpark handles None values properly

    # Create output directory if it doesn't exist
    json_output_path_obj = Path(output_json_path)
    output_dir = json_output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save error blocks to a separate file for debugging if any exist
    error_blocks = (
        results_df[results_df["error"].notna()].copy()
        if len(results_df) > 0 and "error" in results_df.columns
        else pd.DataFrame()
    )

    if len(error_blocks) > 0:
        logger.warning(f"Found {len(error_blocks)} blocks with errors")

    # Backup existing JSON file if it exists
    backup_file(json_output_path_obj)

    # Save to JSON format
    save_jsonl(results_df, json_output_path_obj)

    # Count recovered records by category
    error_recovered_records = 0  # Recovered from BAML API errors
    uuid_recovered_records = 0  # Recovered because BAML dropped them from output
    singleton_records = 0  # Single-company blocks (no matching possible)
    skipped_in_iteration = 0  # All records skipped in this iteration

    if len(results_df) > 0 and "resolved_companies" in results_df.columns:
        for _, row in results_df.iterrows():
            companies = row.get("resolved_companies", [])
            if isinstance(companies, list):
                for company in companies:
                    if isinstance(company, dict):
                        if company.get("match_skip") is True:
                            # Check reason for skip
                            skip_reason = company.get("match_skip_reason", "")
                            if skip_reason == "error_recovery":
                                error_recovered_records += 1
                            elif skip_reason == "missing_in_match_output":
                                uuid_recovered_records += 1
                            elif skip_reason == "singleton_block":
                                singleton_records += 1
                            # Check if this iteration is in the skip history
                            skip_history = company.get("match_skip_history", [])
                            if skip_history and iteration in skip_history:
                                skipped_in_iteration += 1

    # Print summary statistics
    resolved_blocks = (
        results_df[results_df["was_resolved"]]
        if len(results_df) > 0 and "was_resolved" in results_df.columns
        else pd.DataFrame()
    )

    logger.info("=" * 60)
    logger.info("ENTITY RESOLUTION MATCHING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total blocks processed: {len(results_df)}")
    logger.info(f"Successfully resolved: {len(resolved_blocks)}")
    logger.info(f"Errors encountered: {len(error_blocks)}")
    if len(error_blocks) > 0:
        error_path = "data/er/iterations/{iteration}/errors.parquet".format(iteration=iteration)
        logger.info(f"  → Error blocks saved to: {error_path}")
        logger.info(f"  → {error_recovery_count} companies recovered from error blocks")
    logger.info("")
    logger.info("PROCESSING STATISTICS:")
    logger.info(f"  Companies not matched in this iteration: {skipped_in_iteration}")
    logger.info(f"    - Singleton blocks (no matching needed): {singleton_records}")
    logger.info(f"    - Recovered from BAML API errors: {error_recovered_records}")
    logger.info(f"    - Recovered because BAML dropped from output: {uuid_recovered_records}")
    logger.info("")
    logger.info(
        "Note: Resolved companies have new UUIDs; single-company blocks retain original UUIDs"
    )

    if len(resolved_blocks) > 0:
        total_original = resolved_blocks["original_count"].sum()
        total_resolved = resolved_blocks["resolved_count"].sum()
        logger.info("")
        logger.info(f"Total companies before: {total_original}")
        logger.info(f"Total companies after: {total_resolved}")
        logger.info(f"Reduction: {total_original - total_resolved} companies merged")

    logger.info("=" * 60)

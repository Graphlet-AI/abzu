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
from abzu.utils import save_jsonl

logger = get_logger(__name__)

# Initialize collector for BAML tracking
collector = Collector()


async def process_block(
    block: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """
    Process a single block of companies using MultiEntityResolution with UUID mapping.

    Args:
        block: Dictionary containing block data with companies list
        semaphore: Asyncio semaphore for rate limiting

    Returns:
        Dictionary with matched/resolved companies
    """
    async with semaphore:
        # Use the UUID mapping wrapper to process the block
        result: dict[str, Any] = await process_block_with_uuid_mapping(
            block=block,
            baml_client=baml_client,
            collector=collector,
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
) -> list[dict[str, Any]]:
    """
    Process all blocks concurrently with rate limiting.

    Args:
        blocks: List of block dictionaries
        batch_size: Maximum number of concurrent API calls

    Returns:
        List of resolved block dictionaries
    """
    semaphore = asyncio.Semaphore(batch_size)

    # Create tasks for all blocks
    tasks = [process_block(block, semaphore) for block in blocks]

    # Process with progress bar
    results = []
    with tqdm(total=len(tasks), desc="Processing blocks") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            pbar.update(1)

    return results


def backup_file(file_path: Path) -> None:
    """Create a backup of an existing file with timestamp.

    Args:
        file_path: Path to the file to backup
    """
    if file_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")


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
    logger.info(f"Starting entity matching from {blocks_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Batch size: {batch_size}")
    if limit:
        logger.info(f"Limiting to {limit} blocks")
    if min_block_size is not None or max_block_size is not None:
        logger.info(f"Block size range: {min_block_size or 'any'}:{max_block_size or 'any'}")

    # Load blocks from parquet (format the path with iteration and parquet extension)
    blocks_parquet_path = blocks_path.format(iteration=iteration, format="parquet")
    df = pd.read_parquet(blocks_parquet_path)
    logger.info(f"Loaded {len(df)} blocks")

    # Filter to blocks with multiple companies
    multi_company_blocks = df[df["block_size"] > 1].copy()
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
    if len(multi_company_blocks) == 0:
        logger.warning("No blocks found after applying max size filter.")
        return

    # Apply limit if specified
    if limit:
        multi_company_blocks = multi_company_blocks.head(limit)
        logger.info(f"Limited to {len(multi_company_blocks)} blocks")

    # Final check to ensure we have blocks to process
    if len(multi_company_blocks) == 0:
        logger.warning("No blocks to process after applying all filters.")
        return

    # Convert to list of dictionaries for processing
    blocks = cast(list[dict[str, Any]], multi_company_blocks.to_dict("records"))

    # Process blocks asynchronously
    logger.info("Starting async processing...")
    results = asyncio.run(process_blocks_async(blocks, batch_size))

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Format output paths for both formats with iteration
    output_parquet_path = output_path.format(iteration=iteration, format="parquet")
    output_json_path = output_path.format(iteration=iteration, format="json")

    # Create output directory if it doesn't exist
    output_path_obj = Path(output_parquet_path)
    output_dir = output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for blocks with errors and save them separately
    error_blocks = (
        results_df[results_df["error"].notna()]
        if len(results_df) > 0 and "error" in results_df.columns
        else pd.DataFrame()
    )

    if len(error_blocks) > 0:
        # Create error output path
        error_output_path = "data/er/iterations/{iteration}/errors.parquet".format(
            iteration=iteration
        )
        error_path_obj = Path(error_output_path)
        error_dir = error_path_obj.parent
        error_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing error file if it exists
        backup_file(error_path_obj)

        # Save error blocks to separate file
        error_blocks.to_parquet(error_output_path, index=False)
        logger.warning(f"Saved {len(error_blocks)} error blocks to {error_output_path}")

    # Backup existing parquet file if it exists
    backup_file(output_path_obj)

    # Save ALL results to parquet (including error blocks)
    results_df.to_parquet(output_parquet_path, index=False)
    logger.info(f"Saved {len(results_df)} resolved blocks to {output_parquet_path}")

    # Backup existing JSON file if it exists
    json_output_path_obj = Path(output_json_path)
    backup_file(json_output_path_obj)

    # Save to JSON format
    save_jsonl(results_df, json_output_path_obj)

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
    logger.info(f"Errors: {len(error_blocks)}")
    if len(error_blocks) > 0:
        error_path = "data/er/iterations/{iteration}/errors.parquet".format(iteration=iteration)
        logger.info(f"  → Error blocks saved to: {error_path}")
        logger.info("  → Error blocks are still included in main output")
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

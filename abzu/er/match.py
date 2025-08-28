"""Entity resolution matching module using BAML async client."""

import asyncio
from pathlib import Path
from typing import Any, Optional, cast

import pandas as pd
from tqdm import tqdm

from abzu.baml_client.async_client import BamlAsyncClient
from abzu.baml_client.runtime import DoNotUseDirectlyCallManager
from abzu.baml_client.types import Company, CompanyList
from abzu.logs import get_logger

logger = get_logger(__name__)

# Initialize the async client
baml_client = BamlAsyncClient(DoNotUseDirectlyCallManager({}))


async def process_block(
    block: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """
    Process a single block of companies using MultiEntityResolution.

    Args:
        block: Dictionary containing block data with companies list
        semaphore: Asyncio semaphore for rate limiting

    Returns:
        Dictionary with matched/resolved companies
    """
    async with semaphore:
        block_key = block["block_key"]
        companies_data = block["companies"]

        # Skip blocks with only one company
        if len(companies_data) <= 1:
            return {
                "block_key": block_key,
                "block_key_type": block["block_key_type"],
                "resolved_companies": companies_data,
                "total_companies": len(companies_data),
                "was_resolved": False,
            }

        try:
            logger.info(f"Processing block '{block_key}' with {len(companies_data)} companies")

            # Convert to Company objects
            companies = []
            for comp_data in companies_data:
                # Create Company object - id, uuid, and name are required
                company = Company(
                    id=comp_data["id"],  # Required - will raise KeyError if missing
                    uuid=comp_data["uuid"],  # Required - will raise KeyError if missing
                    name=comp_data["name"],  # Required - will raise KeyError if missing
                    description=comp_data.get("description", ""),
                    ceo=comp_data.get("ceo"),
                    employees=comp_data.get("employees"),
                    founded_year=comp_data.get("founded_year"),
                    headquarters_location=comp_data.get("headquarters_location"),
                    linkedin_url=comp_data.get("linkedin_url"),
                    revenue_usd=comp_data.get("revenue_usd"),
                    website_url=comp_data.get("website_url"),
                    ticker=comp_data.get("ticker"),
                    source_ids=comp_data.get("source_ids"),
                    source_uuids=comp_data.get("source_uuids"),
                )
                companies.append(company)

            # Create CompanyList and call BAML function
            company_list = CompanyList(companies=companies)
            logger.debug(f"Submitting block '{block_key}' to MultiEntityResolution API")
            result = await baml_client.MultiEntityResolution(company_list=company_list)

            # Convert resolved companies back to dictionaries
            resolved_companies = []
            for company in result.companies:
                resolved_dict = {
                    "id": company.id,
                    "uuid": company.uuid,
                    "name": company.name,
                    "description": company.description,
                    "ceo": company.ceo,
                    "employees": company.employees,
                    "founded_year": company.founded_year,
                    "headquarters_location": company.headquarters_location,
                    "linkedin_url": company.linkedin_url,
                    "revenue_usd": company.revenue_usd,
                    "website_url": company.website_url,
                    "ticker": company.ticker.__dict__ if company.ticker else None,
                    "source_ids": company.source_ids,
                    "source_uuids": company.source_uuids,
                }
                resolved_companies.append(resolved_dict)

            logger.info(
                f"Resolved block {block_key}: {len(companies_data)} -> {len(resolved_companies)} companies"
            )

            return {
                "block_key": block_key,
                "block_key_type": block["block_key_type"],
                "original_companies": companies_data,
                "resolved_companies": resolved_companies,
                "original_count": len(companies_data),
                "resolved_count": len(resolved_companies),
                "was_resolved": True,
            }

        except KeyError as e:
            logger.error(f"Missing required field in block {block_key}: {e}")
            # Return original companies on error
            return {
                "block_key": block_key,
                "block_key_type": block["block_key_type"],
                "resolved_companies": companies_data,
                "total_companies": len(companies_data),
                "was_resolved": False,
                "error": f"Missing required field: {e}",
            }
        except Exception as e:
            logger.error(f"Error processing block {block_key}: {e}")
            # Return original companies on error
            return {
                "block_key": block_key,
                "block_key_type": block["block_key_type"],
                "resolved_companies": companies_data,
                "total_companies": len(companies_data),
                "was_resolved": False,
                "error": str(e),
            }


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


def match_entities(
    blocks_path: str,
    output_path: str,
    batch_size: int = 5,
    limit: Optional[int] = None,
) -> None:
    """
    Match entities within blocks using BAML MultiEntityResolution.

    Args:
        blocks_path: Path to the blocks parquet file
        output_path: Path to save the matched entities
        batch_size: Number of concurrent API calls
        limit: Maximum number of blocks to process (for testing)
    """
    logger.info(f"Starting entity matching from {blocks_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Batch size: {batch_size}")
    if limit:
        logger.info(f"Limiting to {limit} blocks")

    # Load blocks from parquet
    df = pd.read_parquet(blocks_path)
    logger.info(f"Loaded {len(df)} blocks")

    # Filter to blocks with multiple companies
    multi_company_blocks = df[df["total_companies"] > 1].copy()
    logger.info(f"Found {len(multi_company_blocks)} blocks with multiple companies")

    # Apply limit if specified
    if limit:
        multi_company_blocks = multi_company_blocks.head(limit)
        logger.info(f"Limited to {len(multi_company_blocks)} blocks")

    # Convert to list of dictionaries for processing
    blocks = cast(list[dict[str, Any]], multi_company_blocks.to_dict("records"))

    # Process blocks asynchronously
    logger.info("Starting async processing...")
    results = asyncio.run(process_blocks_async(blocks, batch_size))

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save results to parquet
    results_df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(results_df)} resolved blocks to {output_path}")

    # Print summary statistics
    resolved_blocks = results_df[results_df["was_resolved"]]
    error_blocks = (
        results_df[results_df["error"].notna()] if "error" in results_df.columns else pd.DataFrame()
    )

    logger.info("\nSummary:")
    logger.info(f"  Total blocks processed: {len(results_df)}")
    logger.info(f"  Successfully resolved: {len(resolved_blocks)}")
    logger.info(f"  Errors: {len(error_blocks)}")

    if len(resolved_blocks) > 0:
        total_original = resolved_blocks["original_count"].sum()
        total_resolved = resolved_blocks["resolved_count"].sum()
        logger.info(f"  Total companies before: {total_original}")
        logger.info(f"  Total companies after: {total_resolved}")
        logger.info(f"  Reduction: {total_original - total_resolved} companies merged")

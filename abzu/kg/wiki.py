"""Wikipedia enrichment module for companies."""

import asyncio
import glob
import os
from typing import Any

import aiohttp
from tqdm.asyncio import tqdm as atqdm

from abzu.api.wiki import crawl_company_structured_async
from abzu.config import config
from abzu.logs import get_logger
from abzu.utils import load_jsonl, save_jsonl

logger = get_logger(__name__)


def load_companies(companies_path: str) -> list[dict[str, Any]]:
    """Load companies from JSONL file or Spark output directory.

    Args:
        companies_path: Path to the companies.jsonl file or Spark output directory

    Returns:
        List of company dictionaries
    """
    logger.info(f"Loading companies from {companies_path}")

    # Handle Spark output directory (contains part-*.json files)
    if os.path.isdir(companies_path):
        part_files = glob.glob(os.path.join(companies_path, "part-*.json"))
        if part_files:
            companies: list[dict[str, Any]] = []
            for part_file in sorted(part_files):
                companies.extend(load_jsonl(part_file))
            logger.info(f"Loaded {len(companies):,} companies from Spark output directory")
            return companies

    # Regular JSONL file
    companies = load_jsonl(companies_path)
    logger.info(f"Loaded {len(companies):,} companies")
    return companies


def has_ticker(company: dict[str, Any]) -> bool:
    """Check if a company has a valid ticker.

    Args:
        company: Company dictionary

    Returns:
        True if company has a non-null ticker with a symbol
    """
    ticker = company.get("ticker")
    if not ticker:
        return False
    if isinstance(ticker, dict):
        return bool(ticker.get("symbol"))
    return False


async def enrich_company_with_wiki_async(
    session: aiohttp.ClientSession,
    company: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Async version: Enrich a single company with Wikipedia data.

    Args:
        session: aiohttp ClientSession for making requests
        company: Company dictionary
        semaphore: Semaphore to limit concurrency

    Returns:
        Company dictionary with Wikipedia enrichment applied
    """
    async with semaphore:
        company_name = company.get("name")

        if not company_name:
            logger.warning(f"Company {company.get('uuid', 'unknown')} has no name, skipping")
            return company

        try:
            wiki_data = await crawl_company_structured_async(session, name=company_name)

            # Merge Wikipedia data into company, but don't overwrite existing non-null values
            enriched_company = company.copy()

            # Fields to merge from Wikipedia (only if not already set in company)
            wiki_fields = [
                "description",
                "website_url",
                "headquarters_location",
                "revenue_usd",
                "employees",
                "founded_year",
                "ceo",
                "linkedin_url",
            ]

            for field in wiki_fields:
                wiki_value = wiki_data.get(field)
                company_value = enriched_company.get(field)

                # Only use Wikipedia value if company value is empty/null
                if wiki_value and not company_value:
                    enriched_company[field] = wiki_value
                    logger.debug(f"Enriched {company_name} {field} from Wikipedia")

            return enriched_company

        except Exception as e:
            logger.warning(f"Failed to enrich {company_name} with Wikipedia data: {e}")
            return company


async def process_wiki_async(
    companies_to_enrich: list[dict[str, Any]],
    batch_size: int = 5,
) -> tuple[list[dict[str, Any]], int]:
    """Async processing of Wikipedia enrichment with concurrency control.

    Args:
        companies_to_enrich: List of companies to enrich
        batch_size: Maximum concurrent requests

    Returns:
        Tuple of (enriched_companies, enriched_count)
    """
    semaphore = asyncio.Semaphore(batch_size)
    enriched_companies: list[dict[str, Any]] = []
    enriched_count = 0

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            enrich_company_with_wiki_async(session, company, semaphore)
            for company in companies_to_enrich
        ]

        # Use tqdm.asyncio for async progress bar
        results = await atqdm.gather(*tasks, desc="Enriching with Wikipedia")

        for company, enriched in zip(companies_to_enrich, results):
            enriched_companies.append(enriched)
            if enriched != company:
                enriched_count += 1

    return enriched_companies, enriched_count


def process_wiki(
    companies_path: str = config.get("process.kg.wiki.input"),
    output_path: str = config.get("process.kg.wiki.output"),
    limit: int | None = None,
    tickers_only: bool = True,
    batch_size: int = config.get("process.kg.wiki.concurrent", 5),
) -> int:
    """Enrich companies with Wikipedia data.

    Only processes companies that have tickers, since Wikipedia lookups
    work best with ticker symbols for disambiguation.

    Args:
        companies_path: Path to input companies JSONL file
        output_path: Path to write enriched companies
        limit: Maximum number of companies to process (for testing)
        tickers_only: If True, only process companies with tickers (default: True)
        batch_size: Number of concurrent Wikipedia requests (default: 5)

    Returns:
        0 on success, 1 on failure
    """
    # Load companies
    all_companies = load_companies(companies_path)

    if not all_companies:
        logger.error("No companies to process")
        return 1

    # Filter to companies with tickers if requested
    if tickers_only:
        companies_to_enrich = [c for c in all_companies if has_ticker(c)]
        companies_without_tickers = [c for c in all_companies if not has_ticker(c)]
        logger.info(
            f"Found {len(companies_to_enrich):,} companies with tickers, "
            f"{len(companies_without_tickers):,} without"
        )
    else:
        companies_to_enrich = all_companies
        companies_without_tickers = []

    # Apply limit if specified
    if limit is not None:
        companies_to_enrich = companies_to_enrich[:limit]
        logger.info(f"Limited to {len(companies_to_enrich):,} companies for processing")

    if not companies_to_enrich:
        logger.warning("No companies with tickers to enrich")
        # Still save all companies (unchanged) to output
        if save_jsonl(all_companies, output_path, create_backup=True):
            logger.info(f"Saved {len(all_companies):,} companies (unchanged) to {output_path}")
        return 0

    logger.info(
        f"Processing {len(companies_to_enrich):,} companies for Wikipedia enrichment "
        f"(batch_size={batch_size})"
    )

    # Run async enrichment
    enriched_companies, enriched_count = asyncio.run(
        process_wiki_async(companies_to_enrich, batch_size=batch_size)
    )

    logger.info(f"Enriched {enriched_count:,} companies with Wikipedia data")

    # Combine enriched companies with those without tickers
    final_companies = enriched_companies + companies_without_tickers
    logger.info(f"Total companies to save: {len(final_companies):,}")

    # Save results
    if save_jsonl(final_companies, output_path, create_backup=True):
        logger.info(f"Saved enriched companies to {output_path}")
    else:
        logger.error(f"Failed to save results to {output_path}")
        return 1

    return 0

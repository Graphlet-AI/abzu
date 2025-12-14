"""Wikipedia enrichment module for companies."""

import glob
import os
from typing import Any

from tqdm import tqdm

from abzu.api.wiki import crawl_company_structured
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


def enrich_company_with_wiki(company: dict[str, Any]) -> dict[str, Any]:
    """Enrich a single company with Wikipedia data.

    Args:
        company: Company dictionary

    Returns:
        Company dictionary with Wikipedia enrichment applied
    """
    # Get ticker symbol if available
    ticker_symbol = None
    if company.get("ticker"):
        ticker_data = company["ticker"]
        if isinstance(ticker_data, dict):
            ticker_symbol = ticker_data.get("symbol")

    company_name = company.get("name")

    if not ticker_symbol and not company_name:
        logger.warning(f"Company {company.get('uuid', 'unknown')} has no name or ticker, skipping")
        return company

    try:
        wiki_data = crawl_company_structured(ticker=ticker_symbol, name=company_name)

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


def process_wiki(
    companies_path: str = config.get("process.kg.wiki.input"),
    output_path: str = config.get("process.kg.wiki.output"),
    concurrent: int = 5,
) -> int:
    """Enrich companies with Wikipedia data.

    Args:
        companies_path: Path to input companies JSONL file
        output_path: Path to write enriched companies
        concurrent: Number of concurrent requests (not yet used, for future async)

    Returns:
        0 on success, 1 on failure
    """
    # Load companies
    companies = load_companies(companies_path)

    if not companies:
        logger.error("No companies to process")
        return 1

    logger.info(f"Processing {len(companies):,} companies for Wikipedia enrichment")

    # Enrich each company
    enriched_companies: list[dict[str, Any]] = []
    enriched_count = 0

    for company in tqdm(companies, desc="Enriching with Wikipedia"):
        enriched = enrich_company_with_wiki(company)
        enriched_companies.append(enriched)

        # Track if we actually enriched anything
        if enriched != company:
            enriched_count += 1

    logger.info(f"Enriched {enriched_count:,} companies with Wikipedia data")

    # Save results
    if save_jsonl(enriched_companies, output_path, create_backup=True):
        logger.info(f"Saved enriched companies to {output_path}")
    else:
        logger.error(f"Failed to save results to {output_path}")
        return 1

    return 0

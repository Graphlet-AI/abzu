"""Ticker matching module for enriching companies with SEC ticker data."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import Company, CompanyList, Ticker, TickerList
from abzu.config import config
from abzu.logs import get_logger
from abzu.utils import load_jsonl, save_jsonl

logger = get_logger(__name__)

USER_AGENT = "AbzuBot/1.0 (russell.jurney@gmail.com)"


def download_sec_tickers(
    cache_path: str = config.get("process.kg.tickers.cache"),
    url: str = config.get("process.kg.tickers.url"),
    input: str = config.get("process.kg.raw.output"),
    output: str = config.get("process.kg.tickers.output"),
    force: bool = False,
) -> str:
    """Download SEC tickers from SEC EDGAR if not cached.

    Args:
        cache_path: Path to cache the downloaded file
        url: URL to download SEC tickers from
        input: Path to raw KG companies output directory
        output: Path to write companies with tickers
        force: Force re-download even if cached

    Returns:
        Path to the downloaded/cached file
    """
    cache_file = Path(cache_path)

    if cache_file.exists() and not force:
        logger.info(f"Using cached SEC tickers from {cache_path}")
        return cache_path

    logger.info(f"Downloading SEC tickers from {url}")

    cache_file.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()

    with open(cache_path, "w") as f:
        f.write(response.text)

    logger.info(f"Downloaded and cached SEC tickers to {cache_path}")
    return cache_path


def load_tickers(tickers_path: str) -> list[dict[str, Any]]:
    """Load tickers from JSON or JSONL file.

    Supports:
    - SEC company_tickers_exchange.json format: {"fields": [...], "data": [[cik, name, ticker, exchange], ...]}
    - SEC company_tickers.json format: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
    - JSONL format: {"name": ..., "symbol": ..., "exchange": ...}

    Args:
        tickers_path: Path to the tickers file

    Returns:
        List of ticker dictionaries normalized to {cik, symbol, name, exchange} format
    """
    logger.info(f"Loading tickers from {tickers_path}")

    if tickers_path.endswith(".json"):
        with open(tickers_path) as f:
            data = json.load(f)

        # SEC exchange format: {"fields": ["cik", "name", "ticker", "exchange"], "data": [[...], ...]}
        if "fields" in data and "data" in data:
            fields = data["fields"]
            tickers = []
            for row in data["data"]:
                record = dict(zip(fields, row))
                tickers.append(
                    {
                        "cik": record.get("cik"),
                        "symbol": record.get("ticker", ""),
                        "name": record.get("name", ""),
                        "exchange": record.get("exchange"),
                    }
                )
        # Old SEC format: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
        elif isinstance(data, dict) and all(k.isdigit() for k in list(data.keys())[:10]):
            tickers = [
                {
                    "cik": int(v.get("cik_str", 0)) if v.get("cik_str") else None,
                    "symbol": v.get("ticker", ""),
                    "name": v.get("title", ""),
                    "exchange": None,
                }
                for v in data.values()
            ]
        else:
            raise ValueError(f"Unknown JSON format in {tickers_path}")
    else:
        # JSONL format - normalize field names if needed
        raw_tickers = load_jsonl(tickers_path)
        tickers = [
            {
                "cik": t.get("cik"),
                "symbol": t.get("symbol", t.get("ticker", "")),
                "name": t.get("name", t.get("title", "")),
                "exchange": t.get("exchange"),
            }
            for t in raw_tickers
        ]

    logger.info(f"Loaded {len(tickers):,} tickers")
    return tickers


def load_companies(companies_path: str) -> list[dict[str, Any]]:
    """Load companies from Parquet file or directory.

    Args:
        companies_path: Path to the companies.parquet file or Spark output directory

    Returns:
        List of company dictionaries
    """
    import math

    import numpy as np
    import pandas as pd

    logger.info(f"Loading companies from {companies_path}")

    # Pandas read_parquet handles both files and directories
    df = pd.read_parquet(companies_path)

    # Convert to list of dicts
    companies = df.to_dict(orient="records")

    # Replace NaN/NaT with None for Pydantic compatibility
    # Pandas converts null integers to float NaN, which Pydantic rejects
    for company in companies:
        for key, value in company.items():
            if isinstance(value, float) and math.isnan(value):
                company[key] = None
            elif isinstance(value, np.floating) and np.isnan(value):
                company[key] = None
            elif pd.isna(value):
                company[key] = None

    logger.info(f"Loaded {len(companies):,} companies")
    return companies


def convert_to_baml_company(company_dict: dict[str, Any], company_id: int) -> Company:
    """Convert a company dictionary to a BAML Company object.

    Args:
        company_dict: Dictionary with company fields
        company_id: Consecutive integer ID for this company

    Returns:
        BAML Company object
    """
    ticker = None
    if company_dict.get("ticker"):
        ticker_data = company_dict["ticker"]
        if isinstance(ticker_data, dict):
            ticker = Ticker(
                id=ticker_data.get("id"),
                uuid=ticker_data.get("uuid"),
                symbol=ticker_data.get("symbol", ""),
                exchange=ticker_data.get("exchange"),
            )

    return Company(
        id=company_id,
        uuid=company_dict.get("uuid"),
        name=company_dict.get("name", ""),
        cik=company_dict.get("cik"),
        ticker=ticker,
        description=company_dict.get("description", ""),
        website_url=company_dict.get("website_url"),
        headquarters_location=company_dict.get("headquarters_location"),
        jurisdiction=company_dict.get("jurisdiction"),
        revenue_usd=company_dict.get("revenue_usd"),
        employees=company_dict.get("employees"),
        founded_year=company_dict.get("founded_year"),
        ceo=company_dict.get("ceo"),
        linkedin_url=company_dict.get("linkedin_url"),
        source_ids=None,  # Don't use source_ids from previous iterations
        source_uuids=company_dict.get("source_uuids"),
        match_skip=company_dict.get("match_skip"),
        match_skip_reason=company_dict.get("match_skip_reason"),
        match_skip_history=company_dict.get("match_skip_history"),
    )


def convert_to_baml_ticker(ticker_dict: dict[str, Any], ticker_id: int) -> Ticker:
    """Convert a ticker dictionary to a BAML Ticker object.

    Args:
        ticker_dict: Dictionary with cik, name, symbol, and exchange fields
        ticker_id: Unique ID for this ticker

    Returns:
        BAML Ticker object
    """
    return Ticker(
        id=ticker_id,
        uuid=ticker_dict.get("uuid"),
        symbol=ticker_dict.get("symbol", ""),
        exchange=ticker_dict.get("exchange"),
    )


async def match_tickers_batch(
    companies: list[Company],
    tickers: list[Ticker],
) -> list[Company]:
    """Match a batch of companies with tickers using BAML.

    Args:
        companies: List of BAML Company objects
        tickers: List of BAML Ticker objects

    Returns:
        List of Company objects with tickers matched
    """
    company_list = CompanyList(companies=companies)
    ticker_list = TickerList(tickers=tickers)

    try:
        result = await async_b.AddTickersToCompanies(company_list, ticker_list)
        return result.companies
    except Exception as e:
        logger.error(f"Error matching tickers: {e}")
        return companies


def chunk_list(lst: list, num_chunks: int) -> list[list]:
    """Split a list into approximately equal chunks.

    Args:
        lst: List to split
        num_chunks: Number of chunks to create

    Returns:
        List of chunks
    """
    chunk_size = (len(lst) + num_chunks - 1) // num_chunks
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def process_tickers_async(
    companies_path: str,
    tickers_path: str,
    output_path: str,
    url: str = config.get("process.kg.tickers.url"),
    company_batch_size: int = config.get("process.kg.tickers.company_batch_size"),
    ticker_chunks: int = config.get("process.kg.tickers.ticker_chunks", 10),
    limit: int | None = None,
    download: bool = True,
) -> int:
    """Process companies and match them with SEC tickers.

    Splits tickers into chunks (default 10) to reduce context size per LLM call.
    Each company batch is processed against each ticker chunk, ensuring all
    companies are checked against all tickers.

    Args:
        companies_path: Path to companies.jsonl
        tickers_path: Path to cache/load SEC tickers
        output_path: Path to write enriched companies
        url: URL to download SEC tickers from
        company_batch_size: Number of companies per batch (default 100)
        ticker_chunks: Number of chunks to split tickers into (default 10)
        limit: Maximum number of companies to process (for testing)
        download: Whether to download tickers from SEC (uses cache if exists)

    Returns:
        0 on success, 1 on failure
    """
    # Download SEC tickers if requested
    if download:
        tickers_path = download_sec_tickers(cache_path=tickers_path, url=url)

    # Load data
    companies_data = load_companies(companies_path)
    tickers_data = load_tickers(tickers_path)

    # Apply limit if specified
    if limit is not None:
        companies_data = companies_data[:limit]
        logger.info(f"Limited to {len(companies_data):,} companies")

    if not companies_data:
        logger.error("No companies to process")
        return 1

    if not tickers_data:
        logger.error("No tickers to process")
        return 1

    # Convert to BAML objects with consecutive integer IDs
    baml_companies = [convert_to_baml_company(c, i) for i, c in enumerate(companies_data)]

    # Split tickers into chunks
    ticker_data_chunks = chunk_list(tickers_data, ticker_chunks)
    actual_ticker_chunks = len(ticker_data_chunks)

    # Convert each ticker chunk to BAML objects with consecutive IDs within chunk
    baml_ticker_chunks = [
        [convert_to_baml_ticker(t, i) for i, t in enumerate(chunk)] for chunk in ticker_data_chunks
    ]

    # Calculate total LLM calls
    num_company_batches = (len(baml_companies) + company_batch_size - 1) // company_batch_size
    total_llm_calls = num_company_batches * actual_ticker_chunks

    logger.info(f"Processing {len(baml_companies):,} companies with {len(tickers_data):,} tickers")
    logger.info(f"  Company batches: {num_company_batches} (batch size: {company_batch_size})")
    logger.info(
        f"  Ticker chunks: {actual_ticker_chunks} (~{len(tickers_data) // actual_ticker_chunks:,} tickers each)"
    )
    logger.info(f"  Total LLM calls: {total_llm_calls:,}")

    # Track results - company_id -> best matched company (with ticker if found)
    company_results: dict[int, Company] = {c.id: c for c in baml_companies}

    start_time = time.time()

    # Process each company batch against each ticker chunk
    for i in tqdm(
        range(0, len(baml_companies), company_batch_size),
        desc="Matching tickers",
        total=num_company_batches,
    ):
        company_batch = baml_companies[i : i + company_batch_size]
        batch_num = i // company_batch_size + 1

        for chunk_idx, ticker_chunk in enumerate(baml_ticker_chunks):
            logger.debug(
                f"Processing batch {batch_num}/{num_company_batches} "
                f"with ticker chunk {chunk_idx + 1}/{actual_ticker_chunks}"
            )

            matched = await match_tickers_batch(company_batch, ticker_chunk)

            # Update results - keep ticker if one was matched
            for company in matched:
                if company.ticker is not None:
                    company_results[company.id] = company

    elapsed = time.time() - start_time
    logger.info(f"Processed {len(company_results):,} companies in {elapsed:.2f}s")

    # Collect final results
    all_results = list(company_results.values())

    # Count matches
    matched_count = sum(1 for c in all_results if c.ticker is not None)
    logger.info(
        f"Matched {matched_count:,} companies with tickers ({matched_count * 100 / len(all_results):.1f}%)"
    )

    # Save results
    results_data = [c.model_dump() for c in all_results]
    if save_jsonl(results_data, output_path, create_backup=True):
        logger.info(f"Saved enriched companies to {output_path}")
    else:
        logger.error(f"Failed to save results to {output_path}")
        return 1

    return 0


def process_tickers(
    companies_path: str = config.get("process.kg.tickers.input"),
    tickers_path: str = config.get("process.kg.tickers.cache"),
    output_path: str = config.get("process.kg.tickers.output"),
    url: str = config.get("process.kg.tickers.url"),
    company_batch_size: int = config.get("process.kg.tickers.company_batch_size"),
    ticker_chunks: int = config.get("process.kg.tickers.ticker_chunks", 10),
    limit: int | None = None,
    download: bool = True,
) -> int:
    """Process companies and match them with SEC tickers.

    Downloads tickers from SEC EDGAR if not already cached.
    Splits tickers into chunks to reduce context size per LLM call.

    Args:
        companies_path: Path to companies.jsonl or companies.parquet
        tickers_path: Path to cache/load SEC tickers
        output_path: Path to write enriched companies
        url: URL to download SEC tickers from
        company_batch_size: Number of companies per batch
        ticker_chunks: Number of chunks to split tickers into (default 10)
        limit: Maximum number of companies to process (for testing)
        download: Whether to download tickers from SEC (uses cache if exists)

    Returns:
        0 on success, 1 on failure
    """
    return asyncio.run(
        process_tickers_async(
            companies_path,
            tickers_path,
            output_path,
            url,
            company_batch_size,
            ticker_chunks,
            limit,
            download,
        )
    )

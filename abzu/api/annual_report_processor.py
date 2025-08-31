"""Utilities for processing SEC annual reports with BAML."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd

from abzu.api.sec_downloader import (
    download_annual_report,
    get_cik_from_ticker,
    list_recent_filings,
)
from abzu.baml_client.sync_client import b
from abzu.baml_client.types import AnnualReportData
from abzu.config import config
from abzu.spark.ticker_enrichment import _best_match, load_sec_map

logger = logging.getLogger(__name__)


def enrich_company_tickers(data: dict[str, Any], sec_map: dict[str, str] | None = None) -> None:
    """Populate missing ticker information for companies in annual report data.

    Parameters
    ----------
    data:
        Dictionary representation of ``AnnualReportData``.
    sec_map:
        Optional mapping of normalized company names to ticker symbols. If not
        provided, the SEC ticker list will be loaded.
    """

    if sec_map is None:
        sec_map = load_sec_map()

    def update_company(company: dict[str, Any] | None) -> None:
        if not company or company.get("ticker"):
            return
        ticker, score = _best_match(company.get("name", ""), sec_map)
        if ticker and score == 1.0:
            company["ticker"] = {
                "name": company["name"],
                "symbol": ticker,
                "exchange": None,
            }

    update_company(data.get("reporting_company"))

    for partnership in data.get("partnerships", []) or []:
        update_company(partnership.get("company1"))
        update_company(partnership.get("company2"))

    for investment in data.get("investments", []) or []:
        update_company(investment.get("investor_company"))
        update_company(investment.get("invested_company"))

    for supplier in data.get("suppliers", []) or []:
        update_company(supplier.get("customer_company"))
        update_company(supplier.get("supplier_company"))

    for subsidiary in data.get("subsidiaries", []) or []:
        update_company(subsidiary.get("parent_company"))


def process_annual_report(
    ticker: str,
    year: int,
    output_dir: str = config.get("api.sec.download.annual_reports"),
) -> str:
    """Download and process a company's annual report with BAML.

    Parameters
    ----------
    ticker:
        Stock ticker symbol.
    year:
        Filing year to download.
    output_dir:
        Directory where the report text and processed output will be saved.

    Returns
    -------
    str
        Path to the processed JSON file.
    """
    text_path = download_annual_report(ticker, year, save_dir=output_dir)
    with open(text_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    logger.info("Processing annual report %s %s", ticker, year)
    result: AnnualReportData = b.ExtractCompanyRelationshipsFromAnnualReport(report_text)

    data = result.model_dump()
    enrich_company_tickers(data)

    base_name = Path(text_path).stem
    processed_path = os.path.join(os.path.dirname(text_path), f"processed_{base_name}.json")
    with open(processed_path, "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=2)

    logger.info("Saved processed annual report to %s", processed_path)
    return processed_path


def process_annual_report_data_only(
    ticker: str,
    year: int,
    output_dir: str = config.get("api.sec.download.annual_reports"),
) -> dict[str, Any]:
    """Download and process a company's annual report with BAML, return data only.

    Parameters
    ----------
    ticker:
        Stock ticker symbol.
    year:
        Filing year to download.
    output_dir:
        Directory where the report text will be downloaded (for caching).

    Returns
    -------
    dict[str, Any]
        Processed annual report data.
    """
    text_path = download_annual_report(ticker, year, save_dir=output_dir)
    with open(text_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    logger.info("Processing annual report %s %s", ticker, year)
    result: AnnualReportData = b.ExtractCompanyRelationshipsFromAnnualReport(report_text)

    data = result.model_dump()
    enrich_company_tickers(data)

    # Add metadata
    data["ticker"] = ticker
    data["year"] = year
    data["source_file"] = str(text_path)

    return data


def _extract_related_tickers(data: dict[str, Any]) -> list[str]:
    """Return a list of ticker symbols referenced in ``data``."""

    tickers: set[str] = set()

    def add(company: dict[str, Any] | None) -> None:
        if not company:
            return
        ticker = company.get("ticker")
        if isinstance(ticker, dict):
            symbol = ticker.get("symbol")
            if symbol:
                tickers.add(symbol.upper())

    add(data.get("reporting_company"))

    for partnership in data.get("partnerships", []) or []:
        add(partnership.get("company1"))
        add(partnership.get("company2"))

    for investment in data.get("investments", []) or []:
        add(investment.get("investor_company"))
        add(investment.get("invested_company"))

    for supplier in data.get("suppliers", []) or []:
        add(supplier.get("customer_company"))
        add(supplier.get("supplier_company"))

    for subsidiary in data.get("subsidiaries", []) or []:
        add(subsidiary.get("parent_company"))

    return list(tickers)


def _latest_10k_year(ticker: str) -> int:
    """Return the filing year of the most recent 10-K for ``ticker``."""

    cik = get_cik_from_ticker(ticker)
    filings = list_recent_filings(cik, form_type="10-K", count=1)
    if not filings:
        raise ValueError(f"No 10-K filing found for {ticker}")
    year: int = filings[0]["filing_date_obj"].year
    return year


async def process_annual_report_data_async(
    ticker: str,
    year: int,
    output_dir: str,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any] | None:
    """Download and process a company's annual report with BAML asynchronously, return data only.

    Parameters
    ----------
    ticker:
        Stock ticker symbol.
    year:
        Filing year to download.
    output_dir:
        Directory where the report text will be downloaded (for caching).
    semaphore:
        Asyncio semaphore for rate limiting.

    Returns
    -------
    dict[str, Any] | None
        Processed annual report data, or None if processing failed.
    """
    async with semaphore:
        try:
            # Run the sync function in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            report_data = await loop.run_in_executor(
                None, process_annual_report_data_only, ticker, year, output_dir
            )
            return report_data
        except Exception as exc:
            logger.error("Failed to process %s: %s", ticker, exc)
            return None


def save_annual_reports_data(
    reports_data: list[dict[str, Any]],
    jsonl_path: str,
    parquet_path: str,
) -> None:
    """Save annual reports data to JSON Lines and Parquet formats.

    Parameters
    ----------
    reports_data:
        List of processed annual report data dictionaries.
    jsonl_path:
        Path to save JSON Lines file.
    parquet_path:
        Path to save Parquet file.
    """
    if not reports_data:
        logger.warning("No annual reports data to save")
        return

    # Create DataFrame
    df = pd.DataFrame(reports_data)

    # Create output directories if they don't exist
    Path(jsonl_path).parent.mkdir(parents=True, exist_ok=True)
    Path(parquet_path).parent.mkdir(parents=True, exist_ok=True)

    # Save JSON Lines using pandas
    df.to_json(jsonl_path, orient="records", lines=True)

    # Save as Parquet
    df.to_parquet(parquet_path, index=False)

    logger.info("Saved %d annual reports to %s", len(reports_data), jsonl_path)
    logger.info("Saved %d annual reports to %s", len(reports_data), parquet_path)


def process_annual_reports_bulk_consolidated(
    tickers: list[str],
    output_dir: str,
    jsonl_path: str,
    parquet_path: str,
    batch_size: int = 1,
) -> list[str]:
    """Process annual reports and save consolidated JSON Lines and Parquet files.

    Parameters
    ----------
    tickers:
        List of ticker symbols to process.
    output_dir:
        Directory where individual report text files are stored.
    jsonl_path:
        Path to save consolidated JSON Lines file.
    parquet_path:
        Path to save consolidated Parquet file.
    batch_size:
        Number of concurrent processing tasks (uses async if > 1).

    Returns
    -------
    list[str]
        Symbols of all successfully processed tickers.
    """
    if batch_size > 1:
        return asyncio.run(
            process_annual_reports_bulk_consolidated_async(
                tickers, output_dir, jsonl_path, parquet_path, batch_size
            )
        )

    processed: list[str] = []
    reports_data: list[dict[str, Any]] = []

    for ticker in tickers:
        ticker = ticker.upper()
        try:
            year = _latest_10k_year(ticker)
            report_data = process_annual_report_data_only(ticker, year, output_dir)
            reports_data.append(report_data)
            processed.append(ticker)
        except Exception as exc:
            logger.error("Failed to process %s: %s", ticker, exc)
            continue

    # Save consolidated output
    save_annual_reports_data(reports_data, jsonl_path, parquet_path)
    return processed


def process_annual_reports_bfs_bulk_consolidated(
    tickers: list[str],
    output_dir: str,
    jsonl_path: str,
    parquet_path: str,
    batch_size: int = 1,
) -> list[str]:
    """Process annual reports with BFS and save consolidated JSON Lines and Parquet files.

    Parameters
    ----------
    tickers:
        List of starting ticker symbols.
    output_dir:
        Directory where individual report text files are stored.
    jsonl_path:
        Path to save consolidated JSON Lines file.
    parquet_path:
        Path to save consolidated Parquet file.
    batch_size:
        Number of concurrent processing tasks (uses async if > 1).

    Returns
    -------
    list[str]
        Symbols of all processed tickers.
    """
    if batch_size > 1:
        return asyncio.run(
            process_annual_reports_bfs_bulk_consolidated_async(
                tickers, output_dir, jsonl_path, parquet_path, batch_size
            )
        )

    queue = [t.upper() for t in tickers]
    processed: set[str] = set()
    reports_data: list[dict[str, Any]] = []

    while queue:
        current = queue.pop(0)
        if current in processed:
            continue

        try:
            year = _latest_10k_year(current)
            report_data = process_annual_report_data_only(current, year, output_dir)
            reports_data.append(report_data)
        except Exception as exc:
            logger.error("Failed to process %s: %s", current, exc)
            continue

        processed.add(current)

        # Extract related tickers for BFS expansion
        for sym in _extract_related_tickers(report_data):
            sym = sym.upper()
            if sym not in processed and sym not in queue:
                queue.append(sym)

    # Save consolidated output
    save_annual_reports_data(reports_data, jsonl_path, parquet_path)
    return list(processed)


async def process_annual_reports_bulk_consolidated_async(
    tickers: list[str],
    output_dir: str,
    jsonl_path: str,
    parquet_path: str,
    batch_size: int,
) -> list[str]:
    """Process annual reports with async and save consolidated JSON Lines and Parquet files.

    Parameters
    ----------
    tickers:
        List of ticker symbols to process.
    output_dir:
        Directory where individual report text files are stored.
    jsonl_path:
        Path to save consolidated JSON Lines file.
    parquet_path:
        Path to save consolidated Parquet file.
    batch_size:
        Number of concurrent processing tasks.

    Returns
    -------
    list[str]
        Symbols of all successfully processed tickers.
    """
    semaphore = asyncio.Semaphore(batch_size)
    tasks = []

    for ticker in tickers:
        ticker = ticker.upper()
        try:
            year = _latest_10k_year(ticker)
            task = process_annual_report_data_async(ticker, year, output_dir, semaphore)
            tasks.append((ticker, task))
        except Exception as exc:
            logger.error("Failed to get filing year for %s: %s", ticker, exc)
            continue

    # Process all tasks concurrently
    processed: list[str] = []
    reports_data: list[dict[str, Any]] = []
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

    for (ticker, _), result in zip(tasks, results):
        if isinstance(result, dict):
            processed.append(ticker)
            reports_data.append(result)

    # Save consolidated output
    save_annual_reports_data(reports_data, jsonl_path, parquet_path)
    return processed


async def process_annual_reports_bfs_bulk_consolidated_async(
    tickers: list[str],
    output_dir: str,
    jsonl_path: str,
    parquet_path: str,
    batch_size: int,
) -> list[str]:
    """Process annual reports with BFS and async, save consolidated JSON Lines and Parquet files.

    Parameters
    ----------
    tickers:
        List of starting ticker symbols.
    output_dir:
        Directory where individual report text files are stored.
    jsonl_path:
        Path to save consolidated JSON Lines file.
    parquet_path:
        Path to save consolidated Parquet file.
    batch_size:
        Number of concurrent processing tasks.

    Returns
    -------
    list[str]
        Symbols of all processed tickers.
    """
    queue = [t.upper() for t in tickers]
    processed: set[str] = set()
    reports_data: list[dict[str, Any]] = []
    semaphore = asyncio.Semaphore(batch_size)

    while queue:
        # Process current batch
        current_batch: list[str] = []
        batch_tasks: list[asyncio.Task[dict[str, Any] | None]] = []

        # Prepare batch of tickers to process
        while queue and len(current_batch) < batch_size:
            current = queue.pop(0)
            if current in processed:
                continue

            try:
                year = _latest_10k_year(current)
                task = asyncio.create_task(
                    process_annual_report_data_async(current, year, output_dir, semaphore)
                )
                current_batch.append(current)
                batch_tasks.append(task)
            except Exception as exc:
                logger.error("Failed to get filing year for %s: %s", current, exc)
                continue

        if not batch_tasks:
            break

        # Execute batch concurrently
        results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        # Process results and extract related tickers
        for ticker, result in zip(current_batch, results):
            if isinstance(result, dict):
                processed.add(ticker)
                reports_data.append(result)

                # Extract related tickers for BFS expansion
                for sym in _extract_related_tickers(result):
                    sym = sym.upper()
                    if sym not in processed and sym not in queue:
                        queue.append(sym)

    # Save consolidated output
    save_annual_reports_data(reports_data, jsonl_path, parquet_path)
    return list(processed)

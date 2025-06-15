"""Utilities for processing SEC annual reports with BAML."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

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


def enrich_company_tickers(data: Dict[str, Any], sec_map: Dict[str, str] | None = None) -> None:
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

    def update_company(company: Dict[str, Any] | None) -> None:
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


def process_annual_reports_bfs(ticker: str, year: int, output_dir: str) -> list[str]:
    """Process annual reports in breadth-first order starting from ``ticker``."""

    queue = [ticker.upper()]
    processed: set[str] = set()

    while queue:
        current = queue.pop(0)
        if current in processed:
            continue

        try:
            current_year = year if current == ticker.upper() else _latest_10k_year(current)
            path = process_annual_report(current, current_year, output_dir)
        except Exception as exc:  # noqa: BLE001 - surface errors via log
            logger.error("Failed to process %s: %s", current, exc)
            continue

        processed.add(current)

        try:
            with open(path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to read processed report for %s: %s", current, exc)
            continue

        for sym in _extract_related_tickers(report_data):
            sym = sym.upper()
            if sym not in processed and sym not in queue:
                queue.append(sym)

    return list(processed)


def process_annual_reports_bfs_bulk(tickers: list[str], output_dir: str) -> list[str]:
    """Process annual reports in BFS order starting from ``tickers``.

    Parameters
    ----------
    tickers:
        List of starting ticker symbols.
    output_dir:
        Directory where downloaded and processed reports are stored.

    Returns
    -------
    list[str]
        Symbols of all processed tickers.
    """

    queue = [t.upper() for t in tickers]
    processed: set[str] = set()

    while queue:
        current = queue.pop(0)
        if current in processed:
            continue

        try:
            year = _latest_10k_year(current)
            path = process_annual_report(current, year, output_dir)
        except Exception as exc:  # noqa: BLE001 - surface errors via log
            logger.error("Failed to process %s: %s", current, exc)
            continue

        processed.add(current)

        try:
            with open(path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to read processed report for %s: %s", current, exc)
            continue

        for sym in _extract_related_tickers(report_data):
            sym = sym.upper()
            if sym not in processed and sym not in queue:
                queue.append(sym)

    return list(processed)

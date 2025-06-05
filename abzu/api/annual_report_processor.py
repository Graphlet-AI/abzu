"""Utilities for processing SEC annual reports with BAML."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from abzu.api.sec_downloader import download_annual_report
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

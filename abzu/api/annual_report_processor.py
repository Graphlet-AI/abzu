"""Utilities for processing SEC annual reports with BAML."""

from __future__ import annotations

import json
import os
from pathlib import Path
import logging

from abzu.api.sec_downloader import download_annual_report
from abzu.baml_client.sync_client import b
from abzu.baml_client.types import AnnualReportData
from abzu.config import config

logger = logging.getLogger(__name__)


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

    base_name = Path(text_path).stem
    processed_path = os.path.join(os.path.dirname(text_path), f"processed_{base_name}.json")
    with open(processed_path, "w", encoding="utf-8") as out_file:
        json.dump(result.model_dump(), out_file, indent=2)

    logger.info("Saved processed annual report to %s", processed_path)
    return processed_path


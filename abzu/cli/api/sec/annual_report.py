"""CLI command to download and process SEC annual reports."""

import os

import click

from abzu.api.annual_report_processor import (
    process_annual_report,
    process_annual_reports_bfs_bulk_consolidated,
)
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)

__all__ = ["annual_report"]


@click.command(name="annual-report", context_settings={"show_default": True})
@click.option("-t", "--ticker", required=True, help="Ticker symbol (e.g., AAPL)")
@click.option("-y", "--year", type=int, required=True, help="Filing year")
@click.option(
    "-o",
    "--output-dir",
    default=config.get("api.sec.download.annual_reports"),
    help="Directory to save annual report text",
)
@click.option(
    "--bfs/--no-bfs",
    default=False,
    help="Follow related tickers in breadth-first order",
)
@click.option(
    "--batch-size",
    default=1,
    help="Number of concurrent processing tasks (for BFS mode)",
)
def annual_report(ticker: str, year: int, output_dir: str, bfs: bool, batch_size: int) -> None:
    """Download a 10-K filing and process it with BAML."""

    if bfs:
        # For BFS mode, we'll save the consolidated output with appropriate names
        jsonl_path = os.path.join(output_dir, f"bfs_{ticker}_annual_reports.jsonl")
        parquet_path = os.path.join(output_dir, f"bfs_{ticker}_annual_reports.parquet")

        processed_tickers = process_annual_reports_bfs_bulk_consolidated(
            [ticker], output_dir, jsonl_path, parquet_path, batch_size
        )

        logger.info(
            f"Completed BFS annual report processing for {len(processed_tickers)} companies"
        )
        logger.info(f"Saved consolidated data to {jsonl_path} and {parquet_path}")
        click.secho(
            f"Completed BFS annual report processing for {len(processed_tickers)} companies",
            fg="green",
        )
        click.secho(f"Saved consolidated data to {jsonl_path} and {parquet_path}", fg="green")
    else:
        processed_path = process_annual_report(ticker, year, output_dir)
        logger.info(f"Saved processed annual report to {processed_path}")
        click.secho(f"Saved processed annual report to {processed_path}", fg="green")

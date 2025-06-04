"""CLI command to download SEC annual reports."""

import click

from abzu.api.sec_downloader import download_annual_report
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
def annual_report(ticker: str, year: int, output_dir: str) -> None:
    """Download a 10-K filing and save it as plain text."""

    path = download_annual_report(ticker, year, save_dir=output_dir)
    logger.info(f"Saved annual report to {path}")
    click.secho(f"Saved annual report to {path}", fg="green")

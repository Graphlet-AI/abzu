"""CLI command to download and process SEC annual reports."""

import click

from abzu.config import config

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
    """Download a 10-K filing and process it with BAML."""
    from abzu.api.annual_report_processor import process_annual_report

    processed_path = process_annual_report(ticker, year, output_dir)
    click.secho(f"Saved processed annual report to {processed_path}", fg="green")
    return 0

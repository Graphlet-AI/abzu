"""Commands for working with SEC annual reports."""

import click

from abzu.api.annual_report_kuzu import build_annual_report_kuzu_graph
from abzu.api.annual_report_processor import (
    process_annual_reports_bfs_bulk,
    process_annual_reports_bulk,
)
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group(name="annual-reports")
def annual_reports() -> None:
    """Operations on processed annual reports."""


@annual_reports.group()
def build() -> None:
    """Build resources from annual report data."""


@build.command("kuzu", context_settings={"show_default": True})
@click.option(
    "-i",
    "--input-dir",
    default=config.get("api.sec.download.annual_reports"),
    help="Directory with processed annual reports",
)
@click.option(
    "-o",
    "--output-dir",
    default=config.get("api.sec.build_kuzu.output_dir"),
    help="Directory to write Kuzu CSV files",
)
def build_kuzu(input_dir: str, output_dir: str) -> None:
    """Build a Kuzu graph from processed annual reports."""
    paths = build_annual_report_kuzu_graph(input_dir, output_dir)
    logger.info("Saved companies CSV to %s", paths["companies"])
    for key in (
        "invests_in",
        "has_investor",
        "partnered_with",
        "supplies",
        "has_supplier",
        "subsidiary_of",
        "has_subsidiary",
    ):
        logger.info("Saved %s CSV to %s", key, paths[key])
    click.secho(f"Saved companies CSV to {paths['companies']}", fg="green")
    for key in (
        "invests_in",
        "has_investor",
        "partnered_with",
        "supplies",
        "has_supplier",
        "subsidiary_of",
        "has_subsidiary",
    ):
        click.secho(f"Saved {key} CSV to {paths[key]}", fg="green")


@annual_reports.command("bulk", context_settings={"show_default": True})
@click.option(
    "-i",
    "--input-file",
    "tickers_file",
    default=config.get("process.kg.raw.output") + "/tickers.parquet",
    help="Parquet file with ticker data",
)
@click.option(
    "-o",
    "--output-dir",
    default=config.get("api.sec.download.annual_reports"),
    help="Directory to save annual report text",
)
@click.option(
    "--bfs",
    is_flag=True,
    help="Perform BFS expansion from provided tickers to discover related companies",
)
def bulk(tickers_file: str, output_dir: str, bfs: bool) -> None:
    """Process annual reports from tickers in ``tickers_file``.

    By default, processes only the tickers listed in the parquet file.
    With --bfs flag, performs breadth-first search to discover and process related companies.
    """
    try:
        import pandas as pd

        df = pd.read_parquet(tickers_file)
        # Extract unique ticker symbols from the 'symbol' column
        tickers = df["symbol"].dropna().unique().tolist()
        logger.info("Loaded %s unique tickers from %s", len(tickers), tickers_file)
    except Exception as e:
        # Fallback: try to read as text file for backward compatibility
        try:
            with open(tickers_file, "r", encoding="utf-8") as f:
                tickers = [line.strip() for line in f if line.strip()]
            logger.info("Loaded %s tickers from text file %s", len(tickers), tickers_file)
        except Exception:
            raise click.ClickException(f"Failed to read tickers from {tickers_file}: {e}")

    if bfs:
        logger.info("Processing with BFS expansion from %s starting tickers", len(tickers))
        processed = process_annual_reports_bfs_bulk(tickers, output_dir)
    else:
        logger.info("Processing %s tickers without BFS expansion", len(tickers))
        processed = process_annual_reports_bulk(tickers, output_dir)

    logger.info("Processed %s tickers", len(processed))
    click.secho(f"Processed {len(processed)} tickers", fg="green")

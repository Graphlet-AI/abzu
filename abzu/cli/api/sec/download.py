"""CLI command for downloading SEC filings."""

import click

from abzu.config import config


@click.command()
@click.option(
    "-i",
    "--input",
    "tickers_file",
    default=config.get("api.sec.download.tickers_file"),
    help=f"Path to tickers.parquet file (default: {config.get('api.sec.download.tickers_file')})",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default=config.get("api.sec.download.output_dir"),
    help=f"Directory to store downloaded SEC data (default: {config.get('api.sec.download.output_dir')})",
)
@click.option(
    "-f",
    "--filing-index",
    "filing_index",
    type=int,
    default=0,
    help="Index of 10-Q filing to process (0=most recent)",
)
def download(tickers_file, output_dir, filing_index):
    """Download SEC filings for all tickers in the file."""
    from abzu.api.sec_downloader import process_all_tickers

    process_all_tickers(tickers_file, output_dir, filing_index)
    return 0

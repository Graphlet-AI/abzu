"""CLI command for downloading SEC filings."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "tickers_file",
    default=config.get("api.sec.download.tickers_file"),
    help="Path to tickers.parquet file",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default=config.get("api.sec.download.output_dir"),
    help="Directory to store downloaded SEC data",
)
@click.option(
    "-f",
    "--filing-index",
    "filing_index",
    type=int,
    default=0,
    help="Index of filing to process (0=most recent)",
)
@click.option(
    "-t",
    "--form-type",
    "form_type",
    default=config.get("api.sec.download.form_type"),
    help="SEC form type to download (e.g., 10-Q or 10-K)",
)
@click.option(
    "-k",
    "--ticker",
    "ticker",
    default=config.get("api.sec.download.ticker"),
    help="Download filings for a single ticker",
)
def download(tickers_file, output_dir, filing_index, form_type, ticker):
    """Download SEC filings for a single ticker or all tickers in the file."""
    from abzu.api.sec_downloader import process_all_tickers

    process_all_tickers(
        tickers_file=tickers_file,
        output_dir=output_dir,
        filing_index=filing_index,
        form_type=form_type,
        ticker=ticker,
    )
    return 0

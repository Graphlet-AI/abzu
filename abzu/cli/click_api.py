"""API access module for Abzu using Click."""

import logging

import click

from abzu.api.financialdatasets import (
    financialdatasets_facts_main,
    financialdatasets_tickers_main,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def financialdatasets_cli():
    """Financial Datasets API access."""
    pass


@financialdatasets_cli.command()
@click.option("-t", "--ticker", help="Company ticker symbol (e.g., AAPL)")
@click.option("-c", "--cik", help="Company Central Index Key (e.g., 0000320193)")
@click.option(
    "-f",
    "--file",
    "input_file",
    help="Path to JSONL or Parquet file with records containing 'ticker', 'symbol', or 'cik' field",
)
@click.option(
    "-k",
    "--api-key",
    help="API key for Financial Datasets (defaults to FINANCIAL_DATASETS_API_KEY env var)",
)
@click.option(
    "-p",
    "--pretty",
    is_flag=True,
    help="Format JSON output with indentation (only when printing to stdout)",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help="Output file path (if not provided, prints to stdout)",
)
@click.option(
    "-r",
    "--retries",
    "max_retries",
    type=int,
    default=5,
    help="Maximum number of retries for rate-limited requests (429 status code). Defaults to 5.",
)
@click.option(
    "--pause",
    "pause_seconds",
    type=float,
    default=0.5,
    help="Number of seconds to pause between API requests (defaults to 0.5 seconds).",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress bar when processing multiple companies.",
)
def facts(
    ticker,
    cik,
    input_file,
    api_key,
    pretty,
    output_file,
    max_retries,
    pause_seconds,
    no_progress,
):
    """Get company facts from Financial Datasets API.

    Uses exponential backoff retry for rate-limited requests (HTTP 429 status code).
    Pauses between API requests to prevent rate limiting.
    Shows a progress bar when processing multiple companies.

    Output behavior:
    - When using --ticker or --cik (single company): Prints to stdout or writes to file
    - When using --file (multiple companies): Writes to file specified by --output
    """
    # Validate input parameters
    if not ticker and not cik and not input_file:
        logger.error("Either ticker, cik, or input_file parameter is required")
        return 1

    return financialdatasets_facts_main(
        ticker=ticker,
        cik=cik,
        input_file=input_file,
        api_key=api_key,
        pretty=pretty,
        output_file=output_file,
        max_retries=max_retries,
        pause_seconds=pause_seconds,
        show_progress=not no_progress,
    )


@financialdatasets_cli.command()
@click.option(
    "-k",
    "--api-key",
    help="API key for Financial Datasets (defaults to FINANCIAL_DATASETS_API_KEY env var)",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default="data/financialdatasets/tickers.json",
    help="Output file path (default: data/financialdatasets/tickers.json)",
)
@click.option(
    "-p",
    "--pretty",
    is_flag=True,
    help="Format JSON output with indentation",
)
@click.option(
    "-r",
    "--retries",
    "max_retries",
    type=int,
    default=5,
    help="Maximum number of retries for rate-limited requests (429 status code). Defaults to 5.",
)
def tickers(
    api_key,
    output_file,
    pretty,
    max_retries,
):
    """Get all available tickers from Financial Datasets API.

    Retrieves a list of all available ticker symbols and their associated company information
    from the Financial Datasets API and stores them in a JSON file.

    Output is written to the specified file path (default: data/financialdatasets/tickers.json)
    """
    return financialdatasets_tickers_main(
        api_key=api_key,
        output_file=output_file,
        pretty=pretty,
        max_retries=max_retries,
    )


if __name__ == "__main__":
    financialdatasets_cli()

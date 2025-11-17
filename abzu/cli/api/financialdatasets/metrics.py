"""CLI command for retrieving financial metrics from Financial Datasets API."""

import os
from typing import Optional

import click

from abzu.api.financialdatasets import (
    financialdatasets_metrics_main,
    financialdatasets_metrics_multiple_main,
    read_data_file,
)
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option("-t", "--ticker", help="Ticker symbol to get financial metrics for (e.g., AAPL)")
@click.option(
    "-f",
    "--file",
    "--input",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    default=config.get("api.financialdatasets.metrics.input"),
    help="Path to JSONL or Parquet file with records containing 'ticker', 'symbol', or 'cik' field. Use as flag to use default file from config.",
)
@click.option(
    "-P",
    "--period",
    type=click.Choice(["annual", "quarterly", "ttm"]),
    default="annual",
    help="Period for financial metrics (default: annual)",
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=30,
    help="Number of periods to return (default: 30)",
)
@click.option(
    "-w",
    "--workers",
    "max_workers",
    type=int,
    default=5,
    help="Maximum number of parallel workers for API requests when using input file (default: 5)",
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
    help="Format JSON output with indentation",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    help=f"Output file path. If not specified and using input file, defaults to {config.get('api.financialdatasets.metrics.output')}. Otherwise prints to stdout.",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress bar when processing multiple tickers",
)
def metrics(
    ticker: Optional[str],
    input_file: Optional[str],
    period: str,
    limit: int,
    max_workers: int,
    api_key: Optional[str],
    pretty: bool,
    output_file: Optional[str],
    no_progress: bool,
) -> int:
    """Get financial metrics for ticker(s).

    Retrieves financial metrics for a ticker symbol or multiple tickers from an input file
    with the specified period and limit. Supports different periods: annual, quarterly,
    or ttm (trailing twelve months).

    Either specify a single ticker with -t/--ticker or provide an input file with -f/--input-file
    containing records with 'ticker' or 'symbol' fields.

    Default paths:
    - Default input file path: {0}
    - Default output file path when using input file: {1}

    Examples:
        abzu api financialdatasets metrics -t AAPL
        abzu api financialdatasets metrics -t NVDA -P quarterly -l 5 -p -o data/nvda_metrics.json
        abzu api financialdatasets metrics -f data/knowledge_graph/tickers.parquet -P quarterly -o data/financialdatasets/all_metrics.json
    """.format(
        config.get("api.financialdatasets.metrics.input"),
        config.get("api.financialdatasets.metrics.output"),
    )

    # Handle mutually exclusive options
    if ticker and input_file:
        raise click.UsageError(
            "Cannot use --file with --ticker. Choose either file processing or single ticker lookup."
        )

    # Validate that either ticker or input_file is provided
    if not ticker and not input_file:
        # Use default input file path if neither is specified
        logger.info(
            f"No ticker or input file specified, using default input file: {config.get('api.financialdatasets.metrics.input')}"
        )
        print(str(input_file))
        if not os.path.exists(str(input_file)):
            logger.error(f"Default input file does not exist: {input_file}")
            return 1

    # Handle special case for stdout output
    if output_file == "-":
        output_file = None

    # Use default values for API retry/pause behavior
    max_retries = 5
    pause_seconds = 0.5

    # Single ticker mode
    if ticker:
        return financialdatasets_metrics_main(
            ticker=ticker,
            period=period,
            limit=limit,
            api_key=api_key,
            output_file=output_file,
            pretty=pretty,
            max_retries=max_retries,
            pause_seconds=pause_seconds,
        )

    # Multiple tickers mode (input file)
    else:
        # At this point input_file should not be None since we're in the else block
        assert input_file is not None, "Input file is required"

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return 1

        try:
            # Read ticker/symbol from input file
            logger.info(f"Reading tickers from {input_file}")
            ticker_list: list[str] = []

            for record in read_data_file(input_file):
                # Check for ticker or symbol fields
                ticker_val = record.get("ticker") or record.get("symbol")
                if ticker_val and ticker_val not in ticker_list:
                    ticker_list.append(ticker_val)

            logger.info(f"Found {len(ticker_list)} unique tickers")

            if not ticker_list:
                logger.error(
                    f"No valid records with 'ticker' or 'symbol' fields found in {input_file}"
                )
                return 1

            # Set default output file if not provided when using input file
            if output_file is None:
                output_file = config.get("api.financialdatasets.metrics.output")
                logger.info(f"No output file specified, using default: {output_file}")

            # Process multiple tickers using the multiple metrics function
            return financialdatasets_metrics_multiple_main(
                tickers=ticker_list,
                period=period,
                limit=limit,
                api_key=api_key,
                output_file=output_file,
                pretty=pretty,
                max_retries=max_retries,
                pause_seconds=pause_seconds,
                max_workers=max_workers,
                show_progress=not no_progress,
            )

        except Exception as e:
            logger.error(f"Error processing input file: {e}")
            return 1

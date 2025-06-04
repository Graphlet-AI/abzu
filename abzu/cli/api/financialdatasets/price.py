"""CLI command for retrieving historical price data from Financial Datasets API."""

import os
from typing import Optional

import click

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option("-t", "--ticker", help="Ticker symbol to get price data for (e.g., AAPL)")
@click.option(
    "-f",
    "--input",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    flag_value=config.get("api.financialdatasets.price.input"),
    help="Path to JSONL or Parquet file with records containing 'ticker', 'symbol', or 'cik' field. Use as flag to use default file from config.",
)
@click.option(
    "-s",
    "--start-date",
    required=True,
    help="Start date for price data in ISO format (YYYY-MM-DD)",
)
@click.option(
    "-e",
    "--end-date",
    required=True,
    help="End date for price data in ISO format (YYYY-MM-DD)",
)
@click.option(
    "-i",
    "--interval",
    type=click.Choice(["second", "minute", "day", "week", "month", "year"]),
    default="day",
    help="Time interval for price data (default: day)",
)
@click.option(
    "-m",
    "--multiplier",
    "interval_multiplier",
    type=int,
    default=1,
    help="Multiplier for the interval (e.g., 5 for every 5 minutes, default: 1)",
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
    help="Output file path. For single ticker: defaults to stdout. For input file: defaults to config value.",
)
@click.option(
    "--no-progress",
    is_flag=True,
    help="Disable progress bar when processing multiple tickers",
)
def price(
    ticker: Optional[str],
    input_file: Optional[str],
    start_date: str,
    end_date: str,
    interval: str,
    interval_multiplier: int,
    max_workers: int,
    api_key: Optional[str],
    pretty: bool,
    output_file: Optional[str],
    no_progress: bool,
):
    """Get historical price data for ticker(s).

    Retrieves historical stock price data for a ticker symbol or multiple tickers from an input file
    within a date range at the specified time interval.

    Either specify a single ticker with -t/--ticker or provide an input file with -f/--input
    containing records with 'ticker' or 'symbol' fields.

    Required parameters:
    - Either ticker symbol (-t/--ticker) OR input file (-f/--input)
    - Start date (-s/--start-date) in YYYY-MM-DD format
    - End date (-e/--end-date) in YYYY-MM-DD format

    Output behavior:
    - Single ticker mode: outputs to stdout by default (use -o to save to file)
    - Input file mode: outputs to configured default file (use -o to override)

    Examples:
        abzu api financialdatasets price -t AAPL -s 2023-01-01 -e 2023-12-31
        abzu api financialdatasets price -t NVDA -s 2023-01-01 -e 2023-12-31 -i week -p -o data/nvda_prices.json
        abzu api financialdatasets price -f data/knowledge_graph/tickers.parquet -s 2023-01-01 -e 2023-12-31
        abzu api financialdatasets price -f -s 2023-01-01 -e 2023-12-31  # uses default input from config
    """
    from abzu.api.financialdatasets import (
        financialdatasets_price_main,
        financialdatasets_price_multiple_main,
        read_data_file,
    )

    # Handle mutually exclusive options
    if ticker and input_file:
        raise click.UsageError(
            "Cannot use --input with --ticker. Choose either file processing or single ticker lookup."
        )

    # Validate that either ticker or input_file is provided
    if not ticker and not input_file:
        # Use default input file path if neither is specified
        input_file = config.get("api.financialdatasets.price.input")
        logger.info(f"No ticker or input file specified, using default input file: {input_file}")

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
        return financialdatasets_price_main(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            interval_multiplier=interval_multiplier,
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
                output_file = config.get("api.financialdatasets.price.output")
                logger.info(f"No output file specified, using default: {output_file}")

            return financialdatasets_price_multiple_main(
                tickers=ticker_list,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                interval_multiplier=interval_multiplier,
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

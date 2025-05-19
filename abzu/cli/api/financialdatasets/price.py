"""CLI command for retrieving historical price data from Financial Datasets API."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-t", "--ticker", required=True, help="Ticker symbol to get price data for (e.g., AAPL)"
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
    help="Output file path. If not specified, prints to stdout",
)
def price(
    ticker,
    start_date,
    end_date,
    interval,
    interval_multiplier,
    api_key,
    pretty,
    output_file,
):
    """Get historical price data for a ticker.

    Retrieves historical stock price data for a ticker symbol within a date range
    at the specified time interval. Supports various time intervals from seconds to years.

    Required parameters:
    - Ticker symbol (-t/--ticker)
    - Start date (-s/--start-date) in YYYY-MM-DD format
    - End date (-e/--end-date) in YYYY-MM-DD format

    Examples:
        abzu api financialdatasets price -t AAPL -s 2023-01-01 -e 2023-12-31
        abzu api financialdatasets price -t NVDA -s 2023-01-01 -e 2023-12-31 -i week -p -o data/nvda_prices.json
    """
    from abzu.api.financialdatasets import financialdatasets_price_main

    # Handle special case for stdout output
    if output_file == "-":
        output_file = None

    # Use default values for API retry/pause behavior
    max_retries = 5
    pause_seconds = 0.5

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

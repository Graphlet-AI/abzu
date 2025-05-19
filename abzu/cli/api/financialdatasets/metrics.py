"""CLI command for retrieving financial metrics from Financial Datasets API."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-t", "--ticker", required=True, help="Ticker symbol to get financial metrics for (e.g., AAPL)"
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
def metrics(
    ticker,
    period,
    limit,
    api_key,
    pretty,
    output_file,
):
    """Get financial metrics for a ticker.

    Retrieves financial metrics for a ticker symbol with the specified period and limit.
    Supports different periods: annual, quarterly, or ttm (trailing twelve months).

    Required parameters:
    - Ticker symbol (-t/--ticker)

    Examples:
        abzu api financialdatasets metrics -t AAPL
        abzu api financialdatasets metrics -t NVDA -P quarterly -l 5 -p -o data/nvda_metrics.json
    """
    from abzu.api.financialdatasets import financialdatasets_metrics_main

    # Handle special case for stdout output
    if output_file == "-":
        output_file = None

    # Use default values for API retry/pause behavior
    max_retries = 5
    pause_seconds = 0.5

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

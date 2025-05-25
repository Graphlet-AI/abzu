"""CLI command for Financial Datasets tickers API."""

import click

from abzu.api.financialdatasets import financialdatasets_tickers_main


@click.command(context_settings={"show_default": True})
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

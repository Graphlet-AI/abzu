"""CLI command for retrieving company facts from Financial Datasets API."""

import click

from abzu.api.financialdatasets import financialdatasets_facts_main
from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option("-t", "--ticker", help="Company ticker symbol (e.g., AAPL)")
@click.option("-c", "--cik", help="Company Central Index Key (e.g., 0000320193)")
@click.option(
    "-f",
    "--file",
    "--input",
    "input_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    default=config.get("api.financialdatasets.facts.input"),
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
    default=config.get("api.financialdatasets.facts.output"),
    type=click.Path(exists=False, dir_okay=False),
    help=f"Output file path (only used with --file, default: {config.get('api.financialdatasets.facts.output')}). Single company requests with --ticker or --cik always print to stdout.",
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
@click.pass_context
def facts(
    ctx,
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
    - When using --ticker or --cik (single company): Always outputs to stdout
    - When using --file (multiple companies): Outputs to file specified by --output
    - When no options specified: Uses default input file and outputs to default output file
    """
    # Validate mutually exclusive options
    single_company_opts = [ticker, cik]
    single_company_count = sum(1 for opt in single_company_opts if opt)

    # If ticker or cik is specified, we shouldn't use the input file
    if single_company_count > 0:
        if input_file != config.get("api.financialdatasets.facts.input"):
            raise click.UsageError(
                "Cannot use --file with --ticker or --cik. Choose either file processing or single company lookup."
            )
        # Clear input_file if we're doing single company lookup
        input_file = None

    # Handle special case for stdout output
    if output_file == "-":
        output_file = None

    # Use output file when processing from file, otherwise stdout for single company
    effective_output = output_file if input_file else None

    return financialdatasets_facts_main(
        ticker=ticker,
        cik=cik,
        input_file=input_file,
        api_key=api_key,
        pretty=pretty,
        output_file=effective_output,
        max_retries=max_retries,
        pause_seconds=pause_seconds,
        show_progress=not no_progress,
    )

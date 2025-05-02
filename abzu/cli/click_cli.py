"""CLI tools for Abzu using Click."""

import logging
import sys

import click

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Abzu - Industry knowledge extraction."""
    pass


@cli.group()
def process():
    """Process data for knowledge extraction."""
    pass


@process.group()
def articles():
    """Process articles through LLM extraction pipeline."""
    pass


@articles.command(name="semianalysis")
@click.option(
    "-i",
    "--input",
    "input_file",
    default="data/semianalysis.jsonl",
    help="Input JSONL file path (default: data/semianalysis.jsonl)",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default="data/processed_semianalysis.jsonl",
    help="Output JSONL file path (default: data/processed_semianalysis.jsonl)",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=5,
    help="Number of articles to process concurrently (default: 5)",
)
def process_semianalysis(input_file, output_file, batch_size):
    """Process SemiAnalysis articles through LLM extraction pipeline."""
    from abzu.articles.processor import process_main

    return process_main(
        input_file=input_file,
        output_file=output_file,
        batch_size=batch_size,
    )


@process.group()
def kg():
    """Process articles into a knowledge graph."""
    pass


@kg.command()
@click.option(
    "-i",
    "--input",
    "input_file",
    default="data/processed_semianalysis.jsonl",
    help="Input processed articles JSONL file (default: data/processed_semianalysis.jsonl)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="data/knowledge_graph",
    help="Output directory for knowledge graph (default: data/knowledge_graph)",
)
@click.option(
    "-p",
    "--partitions",
    type=int,
    default=4,
    help="Number of Spark partitions (default: 4)",
)
def raw(input_file, output_dir, partitions):
    """Extract raw knowledge graph from processed articles."""
    from abzu.kg.processor import process_raw_kg

    return process_raw_kg(
        input_file=input_file,
        output_dir=output_dir,
        partitions=partitions,
    )


@kg.command()
@click.option(
    "-i",
    "--input",
    "input_dir",
    default="data/knowledge_graph",
    help="Input directory with raw knowledge graph (default: data/knowledge_graph)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="data/refined_knowledge_graph",
    help="Output directory for refined knowledge graph (default: data/refined_knowledge_graph)",
)
@click.option(
    "-p",
    "--partitions",
    type=int,
    default=4,
    help="Number of Spark partitions (default: 4)",
)
def refine(input_dir, output_dir, partitions):
    """Refine knowledge graph by creating bidirectional relationships."""
    from abzu.kg.processor import process_refine_kg

    return process_refine_kg(
        input_dir=input_dir,
        output_dir=output_dir,
        partitions=partitions,
    )


@cli.group()
def crawl():
    """Crawl content from various sources."""
    pass


@crawl.command(name="semianalysis")
@click.option(
    "-u", "--url", help="URL to start crawling from (defaults to predefined archive URLs)"
)
@click.option(
    "-o",
    "--output",
    "output_path",
    default="data/semianalysis.jsonl",
    help="Output JSONL file path (default: data/semianalysis.jsonl)",
)
@click.option("--pages", type=int, default=24, help="Number of pages to crawl (default: 24)")
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=1,
    help="Number of pages to crawl sequentially (default: 1)",
)
@click.option(
    "-c",
    "--concurrent-requests",
    type=int,
    default=1,
    help="Number of concurrent requests per spider (default: 1)",
)
def crawl_semianalysis(url, output_path, pages, batch_size, concurrent_requests):
    """Crawl SemiAnalysis website."""
    from abzu.cli.crawl import crawl_main

    return crawl_main(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
        concurrent_requests=concurrent_requests,
    )


@cli.group()
def api():
    """API access to external data sources."""
    pass


@api.group()
def financialdatasets():
    """Financial Datasets API access."""
    pass


@financialdatasets.command()
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
    default="data/financialdatasets.jsonl",
    help="Output file path (only used with --file, default: data/financialdatasets.jsonl). Single company requests with --ticker or --cik always print to stdout.",
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
    """
    # Display help if no required parameters are provided
    if not ticker and not cik and not input_file:
        click.echo(ctx.get_help())
        return 0

    from abzu.api.financialdatasets import financialdatasets_facts_main

    # Handle special case for stdout output
    if output_file == "-":
        output_file = None

    # Only use the output file when --file is specified, otherwise output to stdout
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


def main() -> int:
    """Main entry point for the abzu command line interface."""
    # Click automatically exits with the return code
    return cli() or 0


if __name__ == "__main__":
    sys.exit(main())

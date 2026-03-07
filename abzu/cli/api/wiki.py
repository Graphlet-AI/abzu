"""CLI commands for Wikipedia crawling."""

import json

import click

from abzu.api.wiki import crawl_company_structured
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "--ticker",
    type=str,
    help="Stock ticker symbol (e.g., NVDA)",
)
@click.option(
    "--name",
    type=str,
    help="Company name (e.g., NVIDIA)",
)
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    default=config.get("process.kg.wiki.input"),
    help="Input JSON Lines file with 'name' or 'ticker' fields.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=config.get("process.kg.wiki.output"),
    help="Output file path for JSON results.",
)
@click.option(
    "--concurrent",
    "-c",
    type=int,
    default=config.get("process.kg.wiki.concurrent"),
    help="Number of concurrent requests for batch processing.",
)
def wiki(ticker: str, name: str, input: str, output: str, concurrent: int) -> int:
    """Crawl Wikipedia page for a company by ticker or name.

    For single company lookups, use --ticker or --name.
    For batch processing, use --input to process a JSONL file of companies
    and enrich them with Wikipedia metadata.
    """
    # Single company lookup mode
    if ticker or name:
        if input and input != config.get("process.kg.wiki.input"):
            raise click.UsageError("Cannot use --ticker/--name with --input")

        try:
            result = crawl_company_structured(name=name or ticker)

            if output and output != config.get("process.kg.wiki.output"):
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
            else:
                print(json.dumps(result, indent=2))
            return 0

        except Exception as e:
            logger.error(f"Failed to crawl Wikipedia: {e}")
            raise click.ClickException(str(e))

    # Batch processing mode - enrich companies with Wikipedia data
    from abzu.kg.wiki import process_wiki

    return process_wiki(
        companies_path=input,
        output_path=output,
        batch_size=concurrent,
    )

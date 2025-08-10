"""CLI commands for Wikipedia crawling."""

import json

import click

from abzu.api.wiki import crawl_company_wikipedia
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
    help="Input JSON Lines file with 'name' or 'ticker' fields",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path for JSON results",
)
def wiki(ticker: str, name: str, input: str, output: str) -> None:
    """Crawl Wikipedia page for a company by ticker or name."""
    if not ticker and not name and not input:
        raise click.UsageError("Either --ticker, --name, or --input must be provided")

    if (ticker or name) and input:
        raise click.UsageError("Cannot use --ticker/--name with --input")

    # Process single company
    if ticker or name:
        try:
            result = crawl_company_wikipedia(ticker=ticker, name=name)

            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
            else:
                print(json.dumps(result, indent=2))

        except Exception as e:
            logger.error(f"Failed to crawl Wikipedia: {e}")
            raise click.ClickException(str(e))

    # Process batch from file
    else:
        results = []

        with open(input, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    # Skip empty lines
                    continue
                try:
                    data = json.loads(line)
                    company_ticker = data.get("ticker")
                    company_name = data.get("name")

                    if not company_ticker and not company_name:
                        logger.warning(
                            f"Line {line_num}: No 'ticker' or 'name' field found, skipping"
                        )
                        continue

                    result = crawl_company_wikipedia(ticker=company_ticker, name=company_name)
                    results.append(result)

                except json.JSONDecodeError as e:
                    logger.error(f"Line {line_num}: Invalid JSON - {e}")
                except Exception as e:
                    logger.error(f"Line {line_num}: Failed to crawl - {e}")

        # Output results
        if output:
            with open(output, "w") as f:
                for result in results:
                    f.write(json.dumps(result) + "\n")
        else:
            for result in results:
                print(json.dumps(result, indent=2))

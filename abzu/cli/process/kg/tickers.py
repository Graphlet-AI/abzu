"""CLI command for matching companies with SEC tickers."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "companies_path",
    type=click.Path(exists=True),
    default=config.get("process.kg.tickers.input"),
    help="Input companies file (JSONL or Parquet) from raw KG.",
)
@click.option(
    "-t",
    "--tickers",
    "tickers_path",
    type=click.Path(),
    default=config.get("process.kg.tickers.cache"),
    help="Path to cache/load SEC tickers (downloaded automatically if missing).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(),
    default=config.get("process.kg.tickers.output"),
    help="Output JSONL file for companies with tickers.",
)
@click.option(
    "-u",
    "--url",
    "url",
    type=str,
    default=config.get("process.kg.tickers.url"),
    help="URL to download SEC tickers from.",
)
@click.option(
    "-b",
    "--batch-size",
    "company_batch_size",
    type=int,
    default=config.get("process.kg.tickers.company_batch_size"),
    help="Number of companies per BAML batch (all tickers sent each batch).",
)
@click.option(
    "-n",
    "--limit",
    "limit",
    type=int,
    default=None,
    help="Maximum number of companies to process (for testing).",
)
@click.option(
    "--download/--no-download",
    default=True,
    help="Download tickers from SEC EDGAR (uses cache if exists).",
)
def tickers(
    companies_path: str,
    tickers_path: str,
    output_path: str,
    url: str,
    company_batch_size: int,
    limit: int | None,
    download: bool,
) -> int:
    """Match companies with SEC tickers using BAML LLM extraction.

    Downloads ticker data from SEC EDGAR automatically and caches it locally.
    Uses the cached file on subsequent runs.
    """
    from abzu.kg.tickers import process_tickers

    return process_tickers(
        companies_path=companies_path,
        tickers_path=tickers_path,
        output_path=output_path,
        url=url,
        company_batch_size=company_batch_size,
        limit=limit,
        download=download,
    )

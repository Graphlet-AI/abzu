"""CLI command for crawling DC Byte blog."""

import click

from abzu.config import config


@click.command(name="dcbyte", context_settings={"show_default": True})
@click.option(
    "-o",
    "--output",
    "output_path",
    default=config.get("crawl.dcbyte.output", "data/articles/dcbyte.jsonl"),
    help="Output JSONL file path",
)
@click.option(
    "--pages",
    type=int,
    default=10,
    help="Number of pages to load (each 'Load More' click is a page)",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=1,
    help="Number of pages to crawl concurrently",
)
def dcbyte(output_path: str, pages: int, batch_size: int) -> int:
    """Crawl DC Byte blog articles using Playwright."""
    from abzu.crawl.dcbyte import crawl_dcbyte

    return crawl_dcbyte(output_path=output_path, pages=pages, batch_size=batch_size)

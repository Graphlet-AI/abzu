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
def dcbyte(output_path, pages):
    """Crawl DC Byte blog articles using Playwright."""
    from abzu.crawl.dcbyte import crawl_dcbyte

    return crawl_dcbyte(output_path=output_path, pages=pages)

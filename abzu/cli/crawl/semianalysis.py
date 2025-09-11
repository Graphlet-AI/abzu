"""CLI command for crawling SemiAnalysis website."""

import click

from abzu.config import config


@click.command(name="semianalysis", context_settings={"show_default": True})
@click.option(
    "-u", "--url", help="URL to start crawling from (defaults to predefined archive URLs)"
)
@click.option(
    "-o",
    "--output",
    "output_path",
    default=config.get("crawl.semianalysis.output"),
    help="Output JSONL file path",
)
@click.option("--pages", type=int, default=24, help="Number of pages to crawl (default: 24)")
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=10,
    help="Number of pages to crawl concurrently (default: 10)",
)
def semianalysis(url, output_path, pages, batch_size):
    """Crawl SemiAnalysis website."""
    from abzu.crawl.semianalysis import crawl_semianalysis

    return crawl_semianalysis(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
    )

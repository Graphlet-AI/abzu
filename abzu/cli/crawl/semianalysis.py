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
    help=f"Output JSONL file path (default: {config.get('crawl.semianalysis.output')})",
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
def semianalysis(url, output_path, pages, batch_size, concurrent_requests):
    """Crawl SemiAnalysis website."""
    from abzu.crawl import crawl_semianalysis

    return crawl_semianalysis(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
        concurrent_requests=concurrent_requests,
    )

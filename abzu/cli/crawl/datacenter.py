"""CLI command for crawling DataCenter Dynamics website."""

import click

from abzu.config import config


@click.command(name="datacenter", context_settings={"show_default": True})
@click.option(
    "-u", "--url", help="URL to start crawling from (defaults to predefined archive URLs)"
)
@click.option(
    "-o",
    "--output",
    "output_path",
    default=config.get("crawl.datacenter.output"),
    help="Output JSONL file path",
)
@click.option("--pages", type=int, default=300, help="Number of pages to crawl (default: 300)")
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=10,
    help="Number of pages to crawl concurrently (default: 10)",
)
def datacenter(url, output_path, pages, batch_size):
    """Crawl DataCenter Dynamics website."""
    from abzu.crawl.datacenter import crawl_datacenter

    return crawl_datacenter(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
    )

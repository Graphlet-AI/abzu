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
def datacenter(url, output_path, pages, batch_size, concurrent_requests):
    """Crawl DataCenter Dynamics website."""
    from abzu.crawl.datacenter import crawl_datacenter

    return crawl_datacenter(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
        concurrent_requests=concurrent_requests,
    )

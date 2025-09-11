"""CLI command for crawling TheInformation RSS feed."""

import click

from abzu.config import config


@click.command(name="theinformation", context_settings={"show_default": True})
@click.option(
    "-o",
    "--output",
    "output_file",
    default=config.get("crawl.theinformation.output"),
    help="Output JSONL file path",
)
@click.option(
    "--cookie",
    help="Raw Cookie header string for authentication (REQUIRED for TheInformation RSS feed)",
)
@click.option(
    "--user-agent",
    default=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    help="User-Agent header",
)
@click.option(
    "--bypass-cf",
    is_flag=True,
    help="Use cloudscraper to bypass Cloudflare protection",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=1,
    help="Number of pages to crawl concurrently",
)
def theinformation(output_file, cookie, user_agent, bypass_cf, batch_size):
    """Crawl TheInformation RSS feed."""
    from abzu.crawl.information import crawl_theinformation

    return crawl_theinformation(
        output_file=output_file,
        cookie=cookie,
        user_agent=user_agent,
        bypass_cf=bypass_cf,
        batch_size=batch_size,
    )

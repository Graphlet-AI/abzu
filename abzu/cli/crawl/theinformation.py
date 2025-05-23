"""CLI command for crawling TheInformation RSS feed."""

import click

from abzu.config import config


@click.command(name="theinformation")
@click.option(
    "-o",
    "--output",
    "output_file",
    default=config.get("crawl.theinformation.output"),
    help=f"Output JSONL file path (default: {config.get('crawl.theinformation.output')})",
)
@click.option(
    "--cookie",
    help="Raw Cookie header string; defaults to browser cookies",
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
@click.option("--bypass-cf", is_flag=True, help="Use cloudscraper to bypass Cloudflare")
def theinformation(output_file, cookie, user_agent, bypass_cf):
    """Crawl TheInformation RSS feed."""
    from abzu.crawl.information import crawl_theinformation

    return crawl_theinformation(
        output_file=output_file,
        cookie=cookie,
        user_agent=user_agent,
        bypass_cf=bypass_cf,
    )

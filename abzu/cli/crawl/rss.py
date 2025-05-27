"""CLI command for crawling generic RSS feeds."""

import click


@click.command(name="rss", context_settings={"show_default": True})
@click.option(
    "-f",
    "--feeds-file",
    default="feeds.txt",
    help="File containing RSS feeds in source:url format",
)
@click.option("-o", "--output-dir", default="data", help="Directory to write JSONL files")
@click.option("--cookie", help="Raw Cookie header string; defaults to browser cookies")
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
def rss(feeds_file, output_dir, cookie, user_agent, bypass_cf):
    """Crawl RSS feeds from a feeds file."""
    from abzu.crawl.rss import crawl_rss

    return crawl_rss(
        feeds_file=feeds_file,
        output_dir=output_dir,
        cookie=cookie,
        user_agent=user_agent,
        bypass_cf=bypass_cf,
    )

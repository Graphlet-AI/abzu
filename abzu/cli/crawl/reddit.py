"""Reddit crawling commands for ticker-based news."""

from pathlib import Path
from typing import Optional

import click

from abzu.reddit.fetcher import RedditFetcher, save_to_jsonl


@click.group()
def reddit() -> None:
    """Reddit data collection commands."""
    pass


@reddit.command()
@click.argument("ticker")
@click.option("--limit", "-l", default=25, help="Number of posts to fetch")
@click.option("--output", "-o", help="Output file path (default: data/reddit_{ticker}.jsonl)")
def ticker(ticker: str, limit: int, output: Optional[str]) -> None:
    """Fetch Reddit news and discussions for a specific ticker symbol."""
    fetcher = RedditFetcher()

    click.echo(f"Searching for ${ticker.upper()} discussions on Reddit...")

    # Get posts from fetcher
    posts = fetcher.fetch_ticker_posts(ticker, limit)

    click.echo(f"Found {len(posts)} unique posts")

    # Save to JSONL
    if not output:
        output = f"data/reddit_{ticker.lower()}.jsonl"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_jsonl(posts, ticker, output_path)

    click.echo(f"Saved {len(posts)} posts about ${ticker.upper()} to {output}")

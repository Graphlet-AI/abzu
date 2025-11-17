"""Reddit crawling commands for ticker-based news."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from abzu.config import config
from abzu.logs import get_logger
from abzu.reddit.fetcher import RedditFetcher

logger = get_logger(__name__)


@click.command()
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True, readable=True, path_type=str),
    default=None,
    help="Input JSONL file with tickers to crawl (mutually exclusive with --ticker)",
)
@click.option(
    "--ticker",
    "-t",
    default=None,
    help="Single ticker symbol to crawl (mutually exclusive with --input)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True, path_type=str),
    default=lambda: config.get("crawl.reddit.output"),
    help="Output JSONL file for Reddit posts",
)
@click.option("--limit", "-l", default=25, help="Number of posts to fetch per ticker")
def reddit(input: Optional[str], ticker: Optional[str], output: str, limit: int) -> None:
    """Crawl Reddit for posts about tickers.

    Use either --input to process multiple tickers from a file, or --ticker for a single ticker.
    """
    # Validate mutually exclusive options
    if input and ticker:
        click.echo("Error: Cannot use both --input and --ticker options together")
        return

    if not input and not ticker:
        # Use default input if neither is specified
        default_input = config.get("crawl.reddit.input")
        if default_input:
            input = default_input
            if input and not Path(input).exists():
                click.echo(f"Error: Default input file not found: {default_input}")
                return
        else:
            click.echo("Error: Must specify either --input or --ticker")
            return

    # Create output directory if needed
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize fetcher and URL extractor
    try:
        fetcher = RedditFetcher()
    except RuntimeError as e:
        click.echo(f"Error: {e}")
        return

    # Determine tickers to process
    tickers = []

    if ticker:
        # Single ticker mode
        tickers = [ticker]
    else:
        # Input file mode
        if input is None:
            raise ValueError("Input parameter is required when ticker is not provided")
        input_path = Path(input)
        with open(input_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Support both 'ticker' and 'symbol' fields
                    ticker_symbol = data.get("ticker") or data.get("symbol")
                    if ticker_symbol:
                        tickers.append(ticker_symbol)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON line: {line.strip()}")
                    continue

    if not tickers:
        click.echo("No tickers found to process")
        return

    click.echo(f"Processing {len(tickers)} ticker(s)")

    # Collect all posts
    all_posts = []
    for ticker_symbol in tickers:
        click.echo(f"\nSearching for ${ticker_symbol.upper()} discussions on Reddit...")
        try:
            posts = fetcher.fetch_ticker_posts(ticker_symbol, limit)
            click.echo(f"Found {len(posts)} unique posts for ${ticker_symbol.upper()}")

            # Add ticker to each post for reference
            for post in posts:
                post["search_ticker"] = ticker_symbol.upper()

            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Error fetching posts for {ticker_symbol}: {e}")
            click.echo(f"Error fetching posts for ${ticker_symbol.upper()}: {e}")
            continue

    # Save all posts to output file
    if all_posts:
        with open(output_path, "a", encoding="utf-8") as f:
            for post in all_posts:
                # Create document matching expected format
                content_parts = [post["title"]]

                if post.get("selftext"):
                    content_parts.append(post["selftext"])

                # Add comments if available
                comments = post.get("comments", [])
                if comments:
                    content_parts.append("Comments:")
                    for comment in comments[:10]:
                        if isinstance(comment, dict):
                            content_parts.append(f"- {comment.get('body', '')}")

                combined_content = " ".join(content_parts)

                # Create Reddit URL
                reddit_url = (
                    f"https://reddit.com{post['permalink']}"
                    if post["permalink"].startswith("/")
                    else post["permalink"]
                )

                document = {
                    "title": post["title"],
                    "url": reddit_url,
                    "collected_at": datetime.now().isoformat() + "Z",
                    "posted_at": post.get("posted_at", post["created_utc"]),
                    "content": combined_content,
                    "ticker": post.get("search_ticker", ""),
                    "subreddit": post.get("subreddit", ""),
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                }

                f.write(json.dumps(document) + "\n")

        click.echo(f"\nSaved {len(all_posts)} total posts to {output}")
    else:
        click.echo("No posts collected")

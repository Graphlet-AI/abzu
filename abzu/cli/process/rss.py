"""CLI command for processing RSS feed articles."""

import click

from abzu.articles.rss_processor import process_rss_feeds
from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--feeds-file",
    default=config.get("process.rss.feeds_file"),
    help="feeds.txt file with source:url pairs",
)
@click.option(
    "-i",
    "--input-dir",
    default=config.get("process.rss.input_dir"),
    type=click.Path(dir_okay=True, file_okay=False),
    help="Directory containing crawled RSS JSONL files",
)
@click.option(
    "-o",
    "--output-dir",
    default=config.get("process.rss.output_dir"),
    type=click.Path(dir_okay=True, file_okay=False),
    help="Directory to write processed JSONL files",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=5,
    help="Number of articles to process concurrently",
)
def rss(feeds_file, input_dir, output_dir, batch_size):
    """Process RSS articles through the LLM extraction pipeline."""
    return process_rss_feeds(
        feeds_file=feeds_file,
        input_dir=input_dir,
        output_dir=output_dir,
        batch_size=batch_size,
    )

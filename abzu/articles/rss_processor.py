import logging
from pathlib import Path
from typing import Optional

from abzu.articles.processor import process_main
from abzu.config import config

logger = logging.getLogger(__name__)


def process_rss_feeds(
    feeds_file: Optional[str] = None,
    input_dir: str = config.get("process.rss.input_dir"),
    output_dir: str = config.get("process.rss.output_dir"),
    batch_size: int = 5,
) -> int:
    """Process all RSS feed articles defined in configuration or a feeds file.

    Parameters
    ----------
    feeds_file:
        Optional path to the feeds.txt file with ``source:url`` pairs.
        If not provided, uses feeds from configuration.
    input_dir:
        Directory where the crawled JSONL files are stored.
    output_dir:
        Directory where processed JSONL files will be written.
    batch_size:
        Number of articles to process concurrently.
    Returns
    -------
    int
        ``0`` on success, ``1`` if any feed processing fails.
    """
    input_base = Path(input_dir)
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    any_failed = False

    # Get feed sources either from file or configuration
    sources = []

    if feeds_file:
        feeds_path = Path(feeds_file)
        if not feeds_path.exists():
            logger.error("Feeds file not found: %s", feeds_file)
            return 1

        for line in feeds_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                logger.warning("Invalid feed entry: %s", line)
                continue
            source, _url = [part.strip() for part in line.split(":", 1)]
            if source:
                sources.append(source)
    else:
        # Use feeds from configuration
        feeds = config.get("crawl.rss.feeds", {})
        if not feeds:
            logger.error("No feeds found in configuration at crawl.rss.feeds")
            return 1
        sources = list(feeds.keys())

    # Process each source
    for source in sources:
        input_file = input_base / f"{source}.jsonl"
        if not input_file.exists():
            logger.warning("Input file not found: %s", input_file)
            any_failed = True
            continue
        output_file = output_base / f"processed_{source}.jsonl"

        logger.info("Processing RSS articles from %s", input_file)
        result = process_main(str(input_file), str(output_file), batch_size)
        if result != 0:
            any_failed = True

    return 1 if any_failed else 0

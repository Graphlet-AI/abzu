from pathlib import Path
from typing import Optional

from abzu.articles.processor import process_main
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


def process_rss_feeds(
    feeds_file: Optional[str] = None,
    input_path: str = config.get("process.rss.input_dir"),
    output_dir: str = config.get("process.rss.output_dir"),
    batch_size: int = 5,
) -> int:
    """Process RSS feed articles from a file, directory, or configuration.

    Parameters
    ----------
    feeds_file:
        Optional path to the feeds.txt file with ``source:url`` pairs.
        If not provided, uses feeds from configuration.
    input_path:
        Path to a single JSONL file or directory containing crawled JSONL files.
    output_dir:
        Directory where processed JSONL files will be written.
    batch_size:
        Number of articles to process concurrently.
    Returns
    -------
    int
        ``0`` on success, ``1`` if any feed processing fails.
    """
    input_path_obj = Path(input_path)
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    # If input is a single file, process it directly
    if input_path_obj.is_file():
        source = input_path_obj.stem  # e.g., "planet-analog" from "planet-analog.jsonl"
        output_file = output_base / f"processed_{source}.jsonl"

        logger.info("Processing single RSS file: %s", input_path_obj)
        return process_main(str(input_path_obj), str(output_file), batch_size)

    # Input is a directory - process multiple sources
    input_base = input_path_obj
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

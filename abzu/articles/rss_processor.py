import logging
from pathlib import Path

from abzu.articles.processor import process_main
from abzu.config import config

logger = logging.getLogger(__name__)


def process_rss_feeds(
    feeds_file: str = config.get("process.rss.feeds_file"),
    input_dir: str = config.get("process.rss.input_dir"),
    output_dir: str = config.get("process.rss.output_dir"),
    batch_size: int = 5,
) -> int:
    """Process all RSS feed articles defined in a feeds file.

    Parameters
    ----------
    feeds_file:
        Path to the feeds.txt file with ``source:url`` pairs.
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
    feeds_path = Path(feeds_file)
    if not feeds_path.exists():
        logger.error("Feeds file not found: %s", feeds_file)
        return 1

    input_base = Path(input_dir)
    output_base = Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    any_failed = False

    for line in feeds_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            logger.warning("Invalid feed entry: %s", line)
            continue
        source, _url = [part.strip() for part in line.split(":", 1)]
        if not source:
            continue

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

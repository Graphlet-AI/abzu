"""Generic RSS feed crawler."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from abzu.config import config
from abzu.crawl.information import DEFAULT_USER_AGENT, build_session, parse_rss_and_save
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor

logger = get_logger(__name__)


def crawl_rss(
    feeds_file: Optional[str] = None,
    output_dir: str = config.get("crawl.rss.output_dir"),
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
) -> int:
    """Crawl multiple RSS feeds defined in configuration or file.

    Parameters
    ----------
    feeds_file:
        Optional path to a text file containing ``source:url`` pairs.
        If not provided, uses feeds from configuration.
    output_dir:
        Directory where ``source.jsonl`` files will be written.
    cookie:
        Optional raw cookie header string used when fetching the feeds.
    user_agent:
        User agent string for HTTP requests.
    bypass_cf:
        Whether to use ``cloudscraper`` to bypass Cloudflare.

    Returns
    -------
    int
        ``0`` on success, ``1`` on failure.
    """
    try:
        session = build_session(user_agent, cookie, bypass_cf)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to build session: %s", e)
        return 1

    # Initialize URLExtractor to filter RSS feed URLs
    url_extractor = URLExtractor()

    # If feeds_file is provided, use it (backward compatibility)
    if feeds_file:
        path = Path(feeds_file)
        if not path.exists():
            logger.error("Feeds file not found: %s", feeds_file)
            return 1

        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                logger.warning("Invalid feed entry: %s", line)
                continue
            source, url = [part.strip() for part in line.split(":", 1)]
            if not source or not url:
                logger.warning("Invalid feed entry: %s", line)
                continue

            # Check if RSS feed URL should be ignored
            if url_extractor.should_ignore_url(url):
                logger.info(f"Skipping ignored RSS feed URL: {url}")
                continue

            output_file = Path(output_dir) / f"{source}.jsonl"
            logger.info("Processing feed %s -> %s", url, output_file)
            try:
                parse_rss_and_save(url, str(output_file), session)
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to process feed %s: %s", url, e)
    else:
        # Use feeds from configuration
        feeds = config.get("crawl.rss.feeds", {})
        if not feeds:
            logger.error("No feeds found in configuration at crawl.rss.feeds")
            return 1

        logger.info(f"Processing {len(feeds)} feeds from configuration")
        for source, url in feeds.items():
            # Check if RSS feed URL should be ignored
            if url_extractor.should_ignore_url(url):
                logger.info(f"Skipping ignored RSS feed URL: {url}")
                continue

            output_file = Path(output_dir) / f"{source}.jsonl"
            logger.info("Processing feed %s -> %s", url, output_file)
            try:
                parse_rss_and_save(url, str(output_file), session)
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to process feed %s: %s", url, e)

    return 0

"""Generic RSS feed crawler."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from abzu.crawl.information import (
    DEFAULT_USER_AGENT,
    build_session,
    parse_rss_and_save,
)

logger = logging.getLogger(__name__)


def crawl_rss(
    feeds_file: str = "feeds.txt",
    output_dir: str = "data",
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
) -> int:
    """Crawl multiple RSS feeds defined in a file.

    Parameters
    ----------
    feeds_file:
        Path to a text file containing ``source:url`` pairs.
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
    path = Path(feeds_file)
    if not path.exists():
        logger.error("Feeds file not found: %s", feeds_file)
        return 1

    try:
        session = build_session(user_agent, cookie, bypass_cf)
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to build session: %s", e)
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

        output_file = Path(output_dir) / f"{source}.jsonl"
        logger.info("Processing feed %s -> %s", url, output_file)
        try:
            parse_rss_and_save(url, str(output_file), session)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to process feed %s: %s", url, e)

    return 0

"""Utilities for crawling TheInformation.com RSS feeds."""

from __future__ import annotations

from typing import Optional

from abzu.config import config
from abzu.crawl.rss import DEFAULT_USER_AGENT, build_session, parse_rss_and_save
from abzu.logs import get_logger

logger = get_logger(__name__)

# TheInformation RSS feed URL (fixed)
RSS_URL = "https://www.theinformation.com/feed"


def crawl_theinformation(
    output_file: str = config.get("crawl.theinformation.output"),
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
) -> int:
    """Crawl TheInformation RSS feed and save articles."""
    try:
        session = build_session(user_agent, cookie, bypass_cf)
        parse_rss_and_save(RSS_URL, output_file, session)
        return 0
    except Exception as e:  # noqa: BLE001
        logger.error("Crawl failed: %s", e)
        return 1

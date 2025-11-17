"""Utilities for crawling TheInformation.com RSS feeds."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from abzu.config import config
from abzu.crawl.rss import DEFAULT_USER_AGENT, parse_rss_and_save, setup_browser
from abzu.logs import get_logger

logger = get_logger(__name__)

# TheInformation RSS feed URL (fixed)
RSS_URL = "https://www.theinformation.com/feed"


async def _crawl_theinformation_async(
    output_file: str,
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
) -> int:
    """Async implementation of TheInformation crawling using Playwright."""
    try:
        browser = await setup_browser(user_agent, cookie)

        # Get min_year from config
        min_year = config.get("crawl.rss.min_year", None)

        # Create directory if it doesn't exist
        output_dir = Path(output_file).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        await parse_rss_and_save(
            RSS_URL, output_file, browser, min_year, bypass_cf, cookie, user_agent
        )
        await browser.close()
        return 0
    except Exception as e:  # noqa: BLE001
        logger.error("Crawl failed: %s", e)
        return 1


def crawl_theinformation(
    output_file: str = config.get("crawl.theinformation.output"),
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
    batch_size: int = 1,
) -> int:
    """Crawl TheInformation RSS feed and save articles."""
    # Note: batch_size is accepted for API consistency but TheInformation uses async internally
    return asyncio.run(_crawl_theinformation_async(output_file, cookie, user_agent, bypass_cf))

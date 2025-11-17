"""Generic RSS feed crawler."""

from __future__ import annotations

import asyncio
import datetime
import os
from pathlib import Path
from typing import Optional

import dateutil.parser
import feedparser
from playwright.async_api import Browser
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright

try:
    import cloudscraper

    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

from abzu.config import config
from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.utils import append_jsonl, build_crawled_url_index

logger = get_logger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)


async def setup_browser(
    user_agent: str = DEFAULT_USER_AGENT,
    cookie_string: Optional[str] = None,
) -> Browser:
    """Create a Playwright browser instance with user agent and cookies."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    # Create context with user agent and additional headers to look more like a real browser
    context = await browser.new_context(
        user_agent=user_agent,
        extra_http_headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        },
    )

    # Add cookies if provided
    if cookie_string:
        cookies = []
        # Parse cookies more carefully to handle different domains
        for pair in cookie_string.split(";"):
            if "=" in pair:
                key, val = pair.strip().split("=", 1)
                # Use both the main domain and subdomain variations
                cookies.extend(
                    [
                        {"name": key, "value": val, "domain": "theinformation.com", "path": "/"},
                        {"name": key, "value": val, "domain": ".theinformation.com", "path": "/"},
                    ]
                )
        try:
            await context.add_cookies(cookies)  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to add some cookies: {e}")
            # Try adding cookies one by one
            for cookie in cookies:
                try:
                    await context.add_cookies([cookie])  # type: ignore
                except Exception:
                    logger.debug(f"Failed to add cookie {cookie['name']}")
                    continue

    return browser


def fetch_rss_with_cloudscraper(
    rss_url: str, cookie_string: Optional[str] = None, user_agent: str = DEFAULT_USER_AGENT
) -> str:
    """Fetch RSS feed using cloudscraper to bypass Cloudflare protection."""
    if not CLOUDSCRAPER_AVAILABLE:
        raise ImportError("cloudscraper not available. Install with: pip install cloudscraper")

    # Create cloudscraper session
    session = cloudscraper.create_scraper(browser={"custom": user_agent})

    # Add cookies if provided
    if cookie_string:
        cookie_dict = {}
        for pair in cookie_string.split(";"):
            if "=" in pair:
                key, val = pair.strip().split("=", 1)
                cookie_dict[key] = val
        session.cookies.update(cookie_dict)

    # Fetch the RSS feed
    response = session.get(rss_url, timeout=15)
    response.raise_for_status()

    # Handle encoding
    content_bytes: bytes = response.content
    try:
        return content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return content_bytes.decode("utf-8", errors="ignore")


async def parse_rss_and_save(
    rss_url: str,
    output_file: str,
    browser: Browser,
    min_year: Optional[int] = None,
    bypass_cf: bool = False,
    cookie_string: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
) -> None:
    """Parse an RSS feed and write entries with full text to JSONL.

    Parameters
    ----------
    rss_url : str
        URL of the RSS feed to parse
    output_file : str
        Path to output JSONL file
    browser : Browser
        Playwright browser instance to use for HTTP requests
    min_year : Optional[int]
        Minimum year for filtering articles by publication date
    """
    # Build index of already crawled URLs
    crawled_urls = build_crawled_url_index(output_file)
    logger.info(f"Found {len(crawled_urls)} previously crawled URLs")

    # Choose fetch method based on bypass_cf option
    text = ""
    if bypass_cf:
        try:
            logger.info(f"Fetching RSS feed with cloudscraper from: {rss_url}")
            text = fetch_rss_with_cloudscraper(rss_url, cookie_string, user_agent)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching RSS feed with cloudscraper from {rss_url}: {e}")
            return
    else:
        # Use Playwright to fetch RSS feed to avoid 403 errors
        try:
            logger.info(f"Fetching RSS feed with Playwright from: {rss_url}")
            page = await browser.new_page()
            response = await page.goto(rss_url, timeout=15000)

            if response and response.status != 200:
                logger.warning(f"RSS feed response status: {response.status}")

            if not response or response.status != 200:
                logger.error(
                    f"Failed to fetch RSS feed from {rss_url}: HTTP {response.status if response else 'No response'}"
                )
                await page.close()
                return

            # Get the text content
            text = await page.content()
            await page.close()

            # If the content looks like HTML instead of RSS/XML, try getting just the text
            if text.strip().startswith("<!DOCTYPE html>") or text.strip().startswith("<html"):
                # The page might be returning HTML instead of raw RSS
                # Try to get the raw response body
                page = await browser.new_page()
                response = await page.goto(rss_url, timeout=15000)
                if response:
                    text = await response.text()
                await page.close()

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching RSS feed from {rss_url}: {e}")
            return
    feed = feedparser.parse(text)
    entries = feed.entries
    if not entries:
        logger.warning("No entries found in feed: %s", rss_url)
        return

    logger.info(f"Found {len(entries)} entries in RSS feed")

    count = 0
    skipped = 0
    backup_created = False

    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for entry in entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))

        # Skip if URL already crawled
        if link in crawled_urls:
            skipped += 1
            logger.debug(f"Skipping already crawled URL: {link}")
            continue

        # No URL filtering needed (previously used url_extractor.should_ignore_url())

        # Parse and filter by publication date if min_year is set
        if min_year and published:
            try:
                pub_date = dateutil.parser.parse(published)
                if pub_date.year < min_year:
                    skipped += 1
                    logger.info(
                        f"Skipping article from {pub_date.year} (before {min_year}): {link}"
                    )
                    continue
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse publication date '{published}': {e}")

        logger.info(f"Crawling: {link}")

        if getattr(entry, "content", None):
            feed_content = entry.content[0].value
        else:
            feed_content = entry.get("summary", "")

        # Initialize variables for content and URLs
        content: str

        try:
            # Use Playwright to fetch the full HTML with JavaScript rendering
            page = await browser.new_page()
            await page.goto(link, timeout=10000)

            # Wait for content to load
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Get the HTML content
            html_content = await page.content()

            # Extract clean text content
            html_extractor = HTMLExtractor()
            content = html_extractor.extract(html_content)

            await page.close()

        except TimeoutError as e:
            logger.error(f"Timeout error fetching {link}: {e}")
            content = ""
        except PlaywrightError as e:
            logger.error(f"Playwright error fetching {link}: {e}")
            content = ""

        collected_at = datetime.datetime.utcnow().isoformat() + "Z"

        record = {
            "title": title,
            "url": link,
            "posted_at": published,
            "feed_content": feed_content,
            "content": content,
            "collected_at": collected_at,
        }

        # Use append_jsonl which handles deduplication and backup
        # Only create backup on first append
        if append_jsonl(record, output_file, create_backup=not backup_created):
            count += 1
            if not backup_created:
                backup_created = True
        else:
            logger.error(f"Failed to save article: {link}")

    logger.info(
        "Processed %s new entries, skipped %s duplicates, saved to %s", count, skipped, output_file
    )


def crawl_rss(
    feeds_file: Optional[str] = None,
    output_dir: str = config.get("crawl.rss.output_dir"),
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
    batch_size: int = 1,
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
    batch_size:
        Number of feeds to crawl concurrently (for API consistency).

    Returns
    -------
    int
        ``0`` on success, ``1`` on failure.
    """
    # Note: batch_size is accepted for API consistency but RSS uses async internally
    return asyncio.run(_crawl_rss_async(feeds_file, output_dir, cookie, user_agent, bypass_cf))


async def _crawl_rss_async(
    feeds_file: Optional[str] = None,
    output_dir: str = config.get("crawl.rss.output_dir"),
    cookie: Optional[str] = None,
    user_agent: str = DEFAULT_USER_AGENT,
    bypass_cf: bool = False,
) -> int:
    """Async implementation of RSS crawling using Playwright."""
    try:
        browser = await setup_browser(user_agent, cookie)
    except PlaywrightError as e:
        logger.error("Failed to setup browser: %s", e)
        return 1

    # Get min_year from config
    min_year = config.get("crawl.rss.min_year", None)

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

            # No RSS feed URL filtering needed (previously used url_extractor.should_ignore_url())

            output_file = Path(output_dir) / f"{source}.jsonl"
            logger.info("Processing feed %s -> %s", url, output_file)
            try:
                await parse_rss_and_save(
                    url, str(output_file), browser, min_year, bypass_cf, cookie, user_agent
                )
            except PlaywrightError as e:
                logger.error("Failed to process feed %s: %s", url, e)
    else:
        # Use feeds from configuration
        feeds = config.get("crawl.rss.feeds", {})
        if not feeds:
            logger.error("No feeds found in configuration at crawl.rss.feeds")
            return 1

        logger.info(f"Processing {len(feeds)} feeds from configuration")
        for source, url in feeds.items():
            # No RSS feed URL filtering needed (previously used url_extractor.should_ignore_url())

            output_file = Path(output_dir) / f"{source}.jsonl"
            logger.info("Processing feed %s -> %s", url, output_file)
            try:
                await parse_rss_and_save(
                    url, str(output_file), browser, min_year, bypass_cf, cookie, user_agent
                )
            except PlaywrightError as e:
                logger.error("Failed to process feed %s: %s", url, e)

    try:
        await browser.close()
    except PlaywrightError as e:
        logger.warning("Failed to close browser: %s", e)

    return 0

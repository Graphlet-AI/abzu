"""Utilities for crawling TheInformation.com RSS feeds."""

from __future__ import annotations

import datetime
import os
from typing import Optional

import browsercookie
import cloudscraper
import feedparser
import requests

from abzu.config import config
from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor
from abzu.utils import append_jsonl, build_crawled_url_index

logger = get_logger(__name__)

# TheInformation RSS feed URL (fixed)
RSS_URL = "https://www.theinformation.com/feed"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)


def build_session(
    user_agent: str = DEFAULT_USER_AGENT,
    cookie_string: Optional[str] = None,
    bypass_cf: bool = False,
) -> requests.Session:
    """Create a requests session optionally using Cloudflare bypass and cookies."""
    session: requests.Session
    if bypass_cf:
        session = cloudscraper.create_scraper(browser={"custom": user_agent})
    else:
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

    if cookie_string:
        cookie_dict = {}
        for pair in cookie_string.split(";"):
            if "=" in pair:
                key, val = pair.strip().split("=", 1)
                cookie_dict[key] = val
        session.cookies.update(cookie_dict)
    else:
        try:
            jar = browsercookie.chrome()
            for cookie in jar:
                session.cookies.set(
                    cookie.name,
                    cookie.value,
                    domain=getattr(cookie, "domain", None),
                    path=getattr(cookie, "path", "/"),
                )
        except Exception:
            logger.warning("browsercookie failed to load cookies; pass --cookie if needed")

    return session


def extract_text_from_url(session: requests.Session, url: str) -> str:
    """Fetch a URL and return extracted article text using HTMLExtractor."""
    resp = session.get(url, timeout=15)
    if resp.status_code != 200:
        logger.debug(f"Response status code: {resp.status_code} for {url}")
    resp.raise_for_status()

    # Use HTMLExtractor to get clean text
    html_extractor = HTMLExtractor()
    extracted_text = html_extractor.extract(resp.text)

    return extracted_text


def parse_rss_and_save(rss_url: str, output_file: str, session: requests.Session) -> None:
    """Parse an RSS feed and write entries with full text to JSONL."""
    # Build index of already crawled URLs
    crawled_urls = build_crawled_url_index(output_file)
    logger.info(f"Found {len(crawled_urls)} previously crawled URLs")

    # Initialize URLExtractor
    url_extractor = URLExtractor()

    try:
        logger.info(f"Fetching RSS feed from: {rss_url}")
        resp = session.get(rss_url, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"RSS feed response status: {resp.status_code}")
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error fetching RSS feed from {rss_url}: {e}")
        return

    raw = resp.content
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="ignore")
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

        # Skip if URL should be ignored
        if url_extractor.should_ignore_url(link):
            skipped += 1
            logger.info(f"Skipping ignored URL: {link}")
            continue

        logger.info(f"Crawling: {link}")

        if getattr(entry, "content", None):
            feed_content = entry.content[0].value
        else:
            feed_content = entry.get("summary", "")

        # Initialize variables for content and URLs
        content: str
        extracted_urls: list[str] = []

        try:
            # Fetch the full HTML first
            resp = session.get(link, timeout=15)
            if resp.status_code != 200:
                logger.debug(f"Response status code: {resp.status_code} for {link}")
            resp.raise_for_status()

            # Extract URLs from HTML before processing
            extracted_urls = url_extractor.extract_urls_from_html(resp.text)

            # Extract clean text content
            html_extractor = HTMLExtractor()
            content = html_extractor.extract(resp.text)

            logger.debug(f"Extracted {len(extracted_urls)} URLs from {link}")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {link}: {e}")
            content = ""
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error fetching {link}: {e}")
            content = ""
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error fetching {link}: {e}")
            content = ""
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to fetch {link}: {type(e).__name__}: {e}")
            content = ""

        collected_at = datetime.datetime.utcnow().isoformat() + "Z"

        record = {
            "title": title,
            "url": link,
            "posted_at": published,
            "feed_content": feed_content,
            "content": content,
            "urls": extracted_urls,
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

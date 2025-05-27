"""Utilities for crawling TheInformation.com RSS feeds."""

from __future__ import annotations

import datetime
import logging
from typing import Optional

import browsercookie
import cloudscraper
import feedparser
import requests
from bs4 import BeautifulSoup

from abzu.utils import append_jsonl, build_crawled_url_index

logger = logging.getLogger(__name__)

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
    """Fetch a URL and return extracted article text."""
    from typing import cast

    from bs4 import Tag

    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    article = soup.find("article")
    # Handle the case where article might be None
    if article is not None:
        # Cast to Tag to satisfy type checker
        paragraphs = cast(Tag, article).find_all("p")
    else:
        paragraphs = soup.find_all("p")
    return " ".join(p.get_text(strip=True) for p in paragraphs)


def parse_rss_and_save(rss_url: str, output_file: str, session: requests.Session) -> None:
    """Parse an RSS feed and write entries with full text to JSONL."""
    # Build index of already crawled URLs
    crawled_urls = build_crawled_url_index(output_file)
    logger.info(f"Found {len(crawled_urls)} previously crawled URLs")

    try:
        resp = session.get(rss_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        logger.error("Error fetching RSS feed: %s", e)
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

    count = 0
    skipped = 0
    backup_created = False

    for entry in entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))

        # Skip if URL already crawled
        if link in crawled_urls:
            skipped += 1
            logger.info(f"Skipping already crawled URL: {link}")
            continue

        if getattr(entry, "content", None):
            feed_content = entry.content[0].value
        else:
            feed_content = entry.get("summary", "")

        try:
            content = extract_text_from_url(session, link)
        except Exception as e:  # noqa: BLE001
            logger.warning("Failed full extract from %s: %s", link, e)
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


def crawl_theinformation(
    output_file: str = "data/theinformation.jsonl",
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

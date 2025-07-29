"""Generic RSS feed crawler."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Optional

import browsercookie
import cloudscraper
import dateutil.parser
import feedparser
import requests

from abzu.config import config
from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor
from abzu.utils import append_jsonl, build_crawled_url_index

logger = get_logger(__name__)

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


def parse_rss_and_save(
    rss_url: str, output_file: str, session: requests.Session, min_year: Optional[int] = None
) -> None:
    """Parse an RSS feed and write entries with full text to JSONL.

    Parameters
    ----------
    rss_url : str
        URL of the RSS feed to parse
    output_file : str
        Path to output JSONL file
    session : requests.Session
        Session to use for HTTP requests
    min_year : Optional[int]
        Minimum year for filtering articles by publication date
    """
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

            # Check if RSS feed URL should be ignored
            if url_extractor.should_ignore_url(url):
                logger.info(f"Skipping ignored RSS feed URL: {url}")
                continue

            output_file = Path(output_dir) / f"{source}.jsonl"
            logger.info("Processing feed %s -> %s", url, output_file)
            try:
                parse_rss_and_save(url, str(output_file), session, min_year)
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
                parse_rss_and_save(url, str(output_file), session, min_year)
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to process feed %s: %s", url, e)

    return 0

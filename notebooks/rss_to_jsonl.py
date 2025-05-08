"""
rss_to_jsonl.py: Extract RSS feed entries and download full articles into a JSONL file using browser-stored cookies.

Dependencies:
    pip install feedparser requests beautifulsoup4 cloudscraper browsercookie

Usage:
    python rss_to_jsonl.py <rss_url> <output_file> [--cookie "name=value;..."] [--user-agent "UA string"] [--bypass-cf]

Options:
  --cookie     Raw Cookie header string if needed (e.g. "ajs_user_id=...; cf_clearance=...;")
  --user-agent Custom User-Agent string (default: Chrome)
  --bypass-cf  Use cloudscraper to bypass Cloudflare anti-bot protections

Description:
This script parses the RSS feed, captures each entry's feed-provided <content> or <summary>,
then downloads the full article text of each entry URL (via <article> or <p> scraping),
and writes title, url, posted_at, feed_content, content, and collected_at into JSONL.

Cookie Handling:
- If --cookie is provided, parses and uses those cookies.
- Otherwise auto-loads cookies from your browser using browsercookie by iterating through the jar.
"""

import argparse
import datetime
import json

import browsercookie
import cloudscraper
import feedparser
import requests
from bs4 import BeautifulSoup


def build_session(user_agent, cookie_string=None, bypass_cf=False):
    """
    Returns a session that handles Cloudflare (if bypass_cf) or a regular requests.Session.
    If cookie_string is provided, parses and uses it; otherwise auto-loads browser cookies into session.cookies.
    """
    if bypass_cf:
        session = cloudscraper.create_scraper(browser={"custom": user_agent})
    else:
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

    if cookie_string:
        # parse and set cookie_string
        cookie_dict = {}
        for pair in cookie_string.split(";"):
            if "=" in pair:
                key, val = pair.strip().split("=", 1)
                cookie_dict[key] = val
        session.cookies.update(cookie_dict)
    else:
        # auto-load from browser cookie jar
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
            print(
                "Warning: browsercookie failed to load; please install and log into your browser."
            )

    return session


def extract_text_from_url(session, url):
    """
    Fetches URL and extracts visible text from <article> tags or falls back to all <p> tags.
    Returns concatenated text.
    """
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    article = soup.find("article")
    paragraphs = article.find_all("p") if article else soup.find_all("p")
    return " ".join(p.get_text(strip=True) for p in paragraphs)


def parse_rss_and_save(rss_url, output_file, session):
    """
    Parses the RSS feed (decoding bytes safely), then for each entry:
      - grabs feed_content (entry.content or entry.summary)
      - downloads content via extract_text_from_url
      - writes a JSON line with title, url, posted_at, feed_content, content, collected_at
    """
    try:
        resp = session.get(rss_url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")
        return

    raw = resp.content
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="ignore")
    feed = feedparser.parse(text)
    entries = feed.entries
    if not entries:
        print(f"No entries found in feed: {rss_url}")
        return

    count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for entry in entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))

            # feed-provided content HTML
            if getattr(entry, "content", None):
                feed_content = entry.content[0].value
            else:
                feed_content = entry.get("summary", "")

            # full article text extraction
            try:
                content = extract_text_from_url(session, link)
            except Exception as e:
                content = ""
                print(f"Warning: Failed full extract from {link}: {e}")

            # timestamp of collection
            collected_at = datetime.datetime.utcnow().isoformat() + "Z"

            record = {
                "title": title,
                "url": link,
                "posted_at": published,
                "feed_content": feed_content,
                "content": content,
                "collected_at": collected_at,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} entries to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Save RSS entries and full article text into JSONL."
    )
    parser.add_argument("rss_url", help="RSS feed URL")
    parser.add_argument("output", help="Output JSONL file")
    parser.add_argument(
        "--cookie", help='Raw Cookie header string; e.g. "name=value; other=val"', default=None
    )
    parser.add_argument(
        "--user-agent",
        help="User-Agent string",
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
    )
    parser.add_argument(
        "--bypass-cf", action="store_true", help="Use cloudscraper to bypass Cloudflare"
    )
    args = parser.parse_args()

    session = build_session(args.user_agent, args.cookie, args.bypass_cf)
    parse_rss_and_save(args.rss_url, args.output, session)


if __name__ == "__main__":
    main()

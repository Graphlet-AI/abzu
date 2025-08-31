#!/usr/bin/env python3
"""Extract blog posts from DC Byte MHTML file."""

import json
import re
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor
from abzu.utils import append_jsonl

logger = get_logger(__name__)


def parse_mhtml(mhtml_path: str) -> str:
    """Parse MHTML file and extract the main HTML content."""
    with open(mhtml_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Find the main HTML content section
    # Look for Content-Type: text/html and extract until next boundary
    html_match = re.search(
        r"Content-Type: text/html.*?\n\n(.*?)(?=------MultipartBoundary|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )

    if html_match:
        html_content = html_match.group(1)
        # Decode quoted-printable encoding
        html_content = html_content.replace("=\n", "")  # Remove soft line breaks
        html_content = html_content.replace("=3D", "=")  # Decode =
        html_content = html_content.replace("=20", " ")  # Decode space
        html_content = html_content.replace("=22", '"')  # Decode "
        html_content = html_content.replace("=27", "'")  # Decode '
        html_content = html_content.replace("=2D", "-")  # Decode -
        html_content = html_content.replace("=2F", "/")  # Decode /
        html_content = html_content.replace("=3A", ":")  # Decode :
        html_content = html_content.replace("=3B", ";")  # Decode ;
        html_content = html_content.replace("=3C", "<")  # Decode <
        html_content = html_content.replace("=3E", ">")  # Decode >
        html_content = html_content.replace("=3F", "?")  # Decode ?

        return html_content

    raise ValueError("Could not find HTML content in MHTML file")


def extract_posts_from_html(html_content: str) -> list[dict[str, Any]]:
    """Extract blog posts from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    posts = []

    logger.info("Searching for blog posts in HTML content...")

    # Strategy 1: Look for links to news-blogs
    news_links = soup.find_all("a", href=re.compile(r"/news-blogs/[^/]+/?$"))
    logger.info(f"Found {len(news_links)} news-blogs links")

    seen_urls = set()

    for link in news_links:
        url = link.get("href")
        if not url:
            continue

        # Make URL absolute
        if url.startswith("/"):
            url = f"https://www.dcbyte.com{url}"

        # Skip if we've seen this URL
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Skip bad URLs (anchor links, etc.)
        if (
            url.endswith("#")
            or "#pll_switcher" in url
            or url == "https://www.dcbyte.com/news-blogs/"
        ):
            continue

        # Extract post info
        post = {"url": url, "title": "", "excerpt": "", "date": "", "image_url": ""}

        # Try to get title from link text first
        title = link.get_text(strip=True)
        if title and title != "Read More" and len(title) > 5:
            post["title"] = title

        # Look for container with more info
        container = link.find_parent(["article", "div", "li"])
        if container:
            # Try to find better title
            if not post["title"]:
                title_elements = container.find_all(
                    ["h1", "h2", "h3", "h4"], class_=re.compile(r"title|heading")
                )
                for title_elem in title_elements:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 5:
                        post["title"] = title_text
                        break

            # Try to find image
            img = container.find("img")
            if img and img.get("src"):
                img_src = img.get("src")
                if img_src.startswith("/"):
                    img_src = f"https://www.dcbyte.com{img_src}"
                post["image_url"] = img_src

            # Try to find date
            date_elem = container.find(class_=re.compile(r"date|time|published"))
            if date_elem:
                post["date"] = date_elem.get_text(strip=True)

            # Try to find excerpt
            excerpt_elem = container.find("p")
            if excerpt_elem:
                excerpt_text = excerpt_elem.get_text(strip=True)
                if excerpt_text and excerpt_text != post["title"] and len(excerpt_text) > 10:
                    post["excerpt"] = (
                        excerpt_text[:200] + "..." if len(excerpt_text) > 200 else excerpt_text
                    )

        # If we still don't have a title, try to extract from URL
        if not post["title"]:
            url_path = urlparse(url).path
            slug = url_path.split("/")[-2] if url_path.endswith("/") else url_path.split("/")[-1]
            post["title"] = slug.replace("-", " ").title()

        posts.append(post)

    # Strategy 2: Look for Essential Grid or other structured content
    # Try to find grid containers
    grid_containers = soup.find_all(
        ["div", "section"], class_=re.compile(r"grid|portfolio|posts|blog")
    )
    logger.info(f"Found {len(grid_containers)} potential grid containers")

    for container in grid_containers:
        container_links = container.find_all("a", href=re.compile(r"/news-blogs/"))
        for link in container_links:
            url = link.get("href")
            if not url or url in seen_urls:
                continue

            if url.startswith("/"):
                url = f"https://www.dcbyte.com{url}"
            seen_urls.add(url)

            # Extract info similar to above
            title = link.get_text(strip=True)
            if not title or title == "Read More":
                # Try parent
                parent = link.find_parent(["div", "article", "li"])
                if parent:
                    title_elem = parent.find(["h1", "h2", "h3", "h4"])
                    if title_elem:
                        title = title_elem.get_text(strip=True)

            if title and len(title) > 5:
                posts.append(
                    {"url": url, "title": title, "excerpt": "", "date": "", "image_url": ""}
                )

    # Remove duplicates based on URL
    unique_posts = {}
    for post in posts:
        if post["url"] not in unique_posts:
            unique_posts[post["url"]] = post

    logger.info(f"Extracted {len(unique_posts)} unique posts")
    return list(unique_posts.values())


def fetch_article_content(url: str) -> Optional[dict[str, Any]]:
    """Fetch content for a single article URL."""
    try:
        from datetime import datetime

        import requests

        logger.info(f"Fetching content for: {url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        html_extractor = HTMLExtractor()
        url_extractor = URLExtractor()

        # Extract text content
        extracted_text = html_extractor.extract(response.text)
        extracted_urls = url_extractor.extract_urls_from_html(response.text)

        # Parse with BeautifulSoup for metadata
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = soup.title.get_text(strip=True) if soup.title else url.split("/")[-1]

        # Extract publication date
        posted_at = None
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="pubdate"]',
            "time[datetime]",
            ".date",
            ".published",
        ]

        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_str = elem.get("content") or elem.get("datetime") or elem.get_text(strip=True)
                if date_str:
                    try:
                        from dateutil import parser

                        # Handle case where date_str might be a list
                        date_text = date_str[0] if isinstance(date_str, list) else date_str
                        posted_at = parser.parse(date_text).isoformat()
                        break
                    except Exception:
                        continue

        return {
            "url": url,
            "list_url": "https://www.dcbyte.com/news-blogs/",
            "title": title,
            "posted_at": posted_at,
            "collected_at": datetime.now().isoformat(),
            "content": extracted_text,
            "urls": extracted_urls,
        }

    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def main():
    """Main extraction function."""
    mhtml_path = "data/DCByte Complete Blog Page.mhtml"
    output_path = "data/articles/dcbyte.jsonl"

    if not Path(mhtml_path).exists():
        logger.error(f"MHTML file not found: {mhtml_path}")
        return

    logger.info(f"Parsing MHTML file: {mhtml_path}")

    try:
        # Parse MHTML and extract HTML
        html_content = parse_mhtml(mhtml_path)
        logger.info(f"Extracted HTML content ({len(html_content)} characters)")

        # Extract posts from HTML
        posts = extract_posts_from_html(html_content)
        logger.info(f"Found {len(posts)} blog posts")

        # Save post list for inspection
        with open("dcbyte_posts_extracted.json", "w") as f:
            json.dump(posts, f, indent=2)
        logger.info("Post list saved to dcbyte_posts_extracted.json")

        # Fetch full content for each post
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        articles_processed = 0
        for i, post in enumerate(posts, 1):
            logger.info(f"Processing post {i}/{len(posts)}: {post['title']}")

            article_data = fetch_article_content(post["url"])
            if article_data:
                # Create backup on first write
                create_backup = articles_processed == 0
                if append_jsonl(article_data, output_path, create_backup):
                    articles_processed += 1
                    if create_backup and Path(f"{output_path}.bak").exists():
                        logger.info(f"Backup created: {output_path}.bak")
                else:
                    logger.error(f"Failed to save article to {output_path}")

            # Be respectful with requests
            import time

            time.sleep(1)

        logger.info(f"Processing complete. Saved {articles_processed} articles to {output_path}")

    except Exception as e:
        logger.error(f"Error processing MHTML file: {e}")
        raise


if __name__ == "__main__":
    main()

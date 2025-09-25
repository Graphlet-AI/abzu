"""URL content fetcher with retry/backoff strategy."""

import re
import time
from datetime import datetime
from typing import Any, Optional, Union

import cloudscraper
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor

logger = get_logger(__name__)


class ContentFetcher:
    """Fetches content from URLs with retry capabilities."""

    def __init__(
        self,
        max_retries: int = 5,
        pause_seconds: float = 0.5,
        timeout: int = 30,
        use_cloudscraper: bool = False,
    ):
        """Initialize the content fetcher with retry capabilities.

        Args:
            max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.
            pause_seconds: Number of seconds to pause between requests to prevent rate limiting.
                Defaults to 0.5 seconds.
            timeout: Request timeout in seconds. Defaults to 30.
            use_cloudscraper: Whether to use cloudscraper instead of requests. Defaults to False.
                Set to True for sites with anti-bot measures.
        """
        self.pause_seconds = pause_seconds
        self.timeout = timeout
        self.use_cloudscraper = use_cloudscraper

        # Configure session with retry capabilities
        if use_cloudscraper:
            self.session = cloudscraper.create_scraper()
        else:
            self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET", "HEAD"],  # Only retry on GET and HEAD
            backoff_factor=1,  # Exponential backoff: 1, 2, 4, 8, 16 seconds
            respect_retry_after_header=True,  # Honor Retry-After header
            raise_on_status=True,  # Raise exception on status codes in status_forcelist
        )

        # Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Initialize HTML extractor
        self.html_extractor = HTMLExtractor()
        # Initialize URL extractor
        self.url_extractor = URLExtractor()

    def extract_title(self, content: str) -> str:
        """Extract the title from HTML content.

        Args:
            content: HTML content as string

        Returns:
            Title string or empty string if not found
        """
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return ""

    def extract_posted_date(self, content: str, url: str) -> Optional[str]:
        """Extract the posted date from HTML content.

        Attempts to find a publication date in the HTML content using common patterns.

        Args:
            content: HTML content as string
            url: The URL, used to detect certain site patterns

        Returns:
            ISO 8601 formatted date string or None if not found
        """
        # Look for common meta tags
        date_patterns = [
            # Standard meta tags
            r'<meta\s+(?:property|name)="(?:article:published_time|datePublished|publication_date)"\s+content="([^"]+)"',
            r'<meta\s+(?:property|name)="(?:og:published_time)"\s+content="([^"]+)"',
            # JSON-LD pattern
            r'"datePublished"\s*:\s*"([^"]+)"',
            # Time tag with pubdate
            r'<time\s+(?:datetime|pubdate)="([^"]+)"',
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, content, re.IGNORECASE)
            if date_match:
                try:
                    # Try to parse the date and return as ISO 8601
                    date_str = date_match.group(1).strip()
                    # Convert to ISO format if needed
                    if "T" not in date_str and date_str.count("-") >= 2:
                        # Simple date without time, add T00:00:00
                        date_str = f"{date_str}T00:00:00+00:00"
                    return date_str
                except Exception as e:
                    logger.warning(f"Failed to parse date: {date_match.group(1)} - {e}")

        return None

    def fetch_url(self, url: str) -> tuple[bool, Union[dict[str, Any], str]]:
        """Fetch content from a URL with retry capabilities.

        Args:
            url: URL to fetch

        Returns:
            Tuple containing:
                - Success status (True/False)
                - Either the article dict (on success) or an error message (on failure)
        """
        # Ensure URL is properly formatted
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Check if URL should be ignored
        if self.url_extractor.should_ignore_url(url):
            logger.info(f"Skipping ignored URL: {url}")
            return False, "URL is from an ignored domain"

        try:
            # Add a pause before making the request to prevent rate limiting
            if self.pause_seconds > 0:
                logger.debug(f"Pausing for {self.pause_seconds} seconds before request")
                time.sleep(self.pause_seconds)

            # Use session with retry configuration
            logger.info(f"Fetching content from URL: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Get content
            html_content = response.text

            # Extract URLs from HTML before processing
            extracted_urls = list(
                dict.fromkeys(self.url_extractor.extract_urls_from_html(html_content))
            )
            logger.info(f"Extracted {len(extracted_urls)} unique URLs from {url}")

            # Extract clean text using HTMLExtractor
            extracted_text = self.html_extractor.extract(html_content)

            # Extract title and posted date from original HTML
            title = self.extract_title(html_content)
            posted_at = self.extract_posted_date(html_content, url)

            # Create article dict according to schema in README
            collected_at = datetime.utcnow().isoformat()
            article = {
                "url": url,
                "title": title,
                "collected_at": collected_at,
                "posted_at": posted_at,
                "content": extracted_text,  # Store extracted text instead of HTML
                "urls": extracted_urls,  # Add extracted URLs
            }

            logger.info(f"Successfully fetched content from {url}")
            return True, article

        except requests.exceptions.RetryError as e:
            logger.error(f"Request failed after multiple retries: {e}")
            return False, f"Request failed after multiple retries: {e}"
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False, f"Request failed: {e}"
        except Exception as e:
            logger.error(f"Unexpected error fetching URL {url}: {e}")
            return False, f"Unexpected error: {e}"

    def close(self) -> None:
        """Close the session."""
        if self.session:
            self.session.close()

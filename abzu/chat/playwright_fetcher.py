"""URL content fetcher using Playwright for better JavaScript rendering."""

import asyncio
import re
from datetime import datetime
from typing import Any, Optional, Union

from playwright.async_api import Browser, Page, async_playwright

from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor

logger = get_logger(__name__)


class PlaywrightFetcher:
    """Fetches content from URLs using Playwright for JavaScript rendering."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout: int = 30,
        headless: bool = True,
        browser_type: str = "chromium",
    ):
        """Initialize the Playwright content fetcher.

        Args:
            max_retries: Maximum number of retries for failed requests. Defaults to 3.
            timeout: Page load timeout in seconds. Defaults to 30.
            headless: Whether to run browser in headless mode. Defaults to True.
            browser_type: Browser to use: 'chromium', 'firefox', or 'webkit'. Defaults to 'chromium'.
        """
        self.max_retries = max_retries
        self.timeout = timeout * 1000  # Convert to milliseconds for Playwright
        self.headless = headless
        self.browser_type = browser_type
        self.browser: Optional[Browser] = None
        self.playwright = None

        # Initialize HTML extractor
        self.html_extractor = HTMLExtractor()
        # Initialize URL extractor
        self.url_extractor = URLExtractor()

    async def initialize(self) -> None:
        """Initialize Playwright and launch browser."""
        if not self.playwright:
            self.playwright = await async_playwright().start()

            # Choose browser based on type
            if self.playwright is None:
                logger.error("Playwright not initialized")
                return

            if self.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                browser_launcher = self.playwright.chromium

            # Launch browser with optimized settings for headless Linux
            self.browser = await browser_launcher.launch(
                headless=self.headless,
                args=(
                    [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ]
                    if self.browser_type == "chromium"
                    else []
                ),
            )
            logger.info(
                f"Playwright browser ({self.browser_type}) initialized in {'headless' if self.headless else 'headed'} mode"
            )

    async def close(self) -> None:
        """Close browser and cleanup Playwright."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("Playwright browser closed")

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
                    date_str = date_match.group(1).strip()
                    # Convert to ISO format if needed
                    if "T" not in date_str and date_str.count("-") >= 2:
                        date_str = f"{date_str}T00:00:00+00:00"
                    return date_str
                except Exception as e:
                    logger.warning(f"Failed to parse date: {date_match.group(1)} - {e}")

        return None

    async def fetch_url(self, url: str) -> tuple[bool, Union[dict[str, Any], str]]:
        """Fetch content from a URL using Playwright.

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

        # Initialize browser if not already done
        if not self.browser:
            await self.initialize()

        if not self.browser:
            return False, "Failed to initialize browser"

        page: Optional[Page] = None
        retries = 0

        while retries < self.max_retries:
            try:
                # Create new page with optimized settings
                page = await self.browser.new_page(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    ignore_https_errors=True,
                )

                # Set extra headers to appear more like a real browser
                await page.set_extra_http_headers(
                    {
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "DNT": "1",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                    }
                )

                logger.info(
                    f"Fetching content from URL: {url} (attempt {retries + 1}/{self.max_retries})"
                )

                # Navigate to the page with timeout
                response = await page.goto(url, wait_until="networkidle", timeout=self.timeout)

                # Check response status
                if response and response.status >= 400:
                    raise Exception(f"HTTP {response.status} error")

                # Wait a bit for any dynamic content to load
                await page.wait_for_timeout(2000)

                # Get the full HTML content
                html_content = await page.content()

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

                # Create article dict according to schema
                collected_at = datetime.utcnow().isoformat()
                article = {
                    "url": url,
                    "title": title,
                    "collected_at": collected_at,
                    "posted_at": posted_at,
                    "content": extracted_text,
                    "urls": extracted_urls,
                }

                logger.info(f"Successfully fetched content from {url}")

                # Close the page
                await page.close()

                return True, article

            except asyncio.TimeoutError:
                retries += 1
                logger.warning(f"Timeout fetching {url} (attempt {retries}/{self.max_retries})")
                if page:
                    await page.close()
                if retries < self.max_retries:
                    await asyncio.sleep(2**retries)  # Exponential backoff

            except Exception as e:
                retries += 1
                logger.error(f"Error fetching {url}: {e} (attempt {retries}/{self.max_retries})")
                if page:
                    await page.close()
                if retries < self.max_retries:
                    await asyncio.sleep(2**retries)  # Exponential backoff

        # All retries exhausted
        error_msg = f"Failed to fetch {url} after {self.max_retries} attempts"
        logger.error(error_msg)
        return False, error_msg

    def fetch_url_sync(self, url: str) -> tuple[bool, Union[dict[str, Any], str]]:
        """Synchronous wrapper for fetch_url for compatibility.

        Args:
            url: URL to fetch

        Returns:
            Same as fetch_url
        """
        # Create new event loop if needed
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.fetch_url(url))

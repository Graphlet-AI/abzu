"""DataCenter Dynamics crawler using Playwright for dynamic content loading."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from numpy.random import default_rng
from playwright.async_api import Page, async_playwright
from tqdm import tqdm

from abzu.config import config
from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor
from abzu.utils import append_jsonl, build_crawled_url_index

logger = get_logger(__name__)


class DataCenterPlaywrightCrawler:
    """Playwright-based crawler for DataCenter Dynamics to bypass anti-bot protection."""

    def __init__(self, output_path: str, max_pages: int = 10):
        """Initialize the DataCenter crawler.

        Args:
            output_path: Path to save crawled articles
            max_pages: Maximum number of pages to crawl
        """
        self.output_path = Path(output_path)
        self.max_pages = max_pages
        self.base_url = "https://www.datacenterdynamics.com"
        self.articles_processed = 0
        self.html_extractor = HTMLExtractor()
        self.url_extractor = URLExtractor()
        self.crawled_urls = build_crawled_url_index(output_path)
        self.rng = default_rng()  # Initialize random number generator
        logger.info(f"Found {len(self.crawled_urls)} previously crawled URLs")

    def get_archive_url(self, page_num: int) -> str:
        """Generate archive URL for a specific page."""
        return f"{self.base_url}/en/news/?page={page_num}"

    async def extract_article_links(self, page: Page) -> list[str]:
        """Extract article links from a DataCenter Dynamics archive page."""
        # Wait for the page to load with timeout
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            logger.warning(f"Network idle timeout, continuing anyway: {e}")

        # Debug: Check page content
        title = await page.title()
        url = page.url
        logger.info(f"Extracting links from page: {title} at {url}")

        # Extract article links using the same selector as the Scrapy crawler
        article_links = await page.evaluate(
            """
            () => {
                // Find all article links using the card structure
                const links = document.querySelectorAll('article.card a.block-link.headline-link');
                const urls = Array.from(links).map(link => link.href);

                // If no links found with specific selector, try fallback
                if (urls.length === 0) {
                    console.log('No links found with specific selector, trying fallback');
                    const fallbackLinks = document.querySelectorAll('a[href*="/en/news/"]');
                    return Array.from(fallbackLinks)
                        .map(link => link.href)
                        .filter(url =>
                            url.includes('/en/news/') &&
                            !url.endsWith('/en/news/') &&
                            !url.includes('?page=')
                        );
                }

                return urls;
            }
            """
        )

        logger.info(f"Found {len(article_links)} article links on page")
        return list(article_links)  # Ensure list type

    async def fetch_article_content(self, page: Page, url: str) -> Optional[dict[str, Any]]:
        """Fetch and extract content from an individual article."""
        try:
            logger.info(f"Fetching article: {url}")

            # Navigate to the article with multiple wait strategies
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for content to be present, but don't wait for full networkidle
                await page.wait_for_selector("body", timeout=10000)
                # Human-like wait for content rendering
                render_delay = int(self.rng.uniform(2000, 5000))
                await page.wait_for_timeout(render_delay)
            except Exception as nav_error:
                logger.warning(f"Navigation timeout for {url}: {nav_error}")
                # Try to check if we at least got some content
                try:
                    title = await page.title()
                    if not title or "403" in title or "error" in title.lower():
                        logger.warning(f"Page appears blocked or empty: {url}")
                        return None
                except (TimeoutError, Exception) as e:
                    logger.error(f"Failed to access page at all: {url} - {e}")
                    return None

            # Check if we got blocked (403 or similar)
            try:
                title = await page.title()
                if "403" in title or "forbidden" in title.lower():
                    logger.warning(f"Got blocked response for {url}")
                    return None
            except (TimeoutError, Exception) as e:
                logger.warning(f"Could not check page title for {url} - {e}")

            # Get the full HTML
            html_content = await page.content()

            # Extract text using HTMLExtractor
            extracted_text = self.html_extractor.extract(html_content)

            # Extract URLs from the article
            extracted_urls = self.url_extractor.extract_urls_from_html(html_content)

            # Extract title
            title = await page.title()

            # Clean up title if it contains site name
            if " | " in title:
                title = title.split(" | ")[0].strip()

            # Try to extract publication date
            posted_at = None
            date_selectors = [
                'meta[property="article:published_time"]',
                "time[datetime]",
                'meta[name="pubdate"]',
                ".date",
                ".meta-date",
                ".published",
            ]

            for selector in date_selectors:
                try:
                    date_elem = await page.query_selector(selector)
                    if date_elem:
                        date_str = (
                            await date_elem.get_attribute("content")
                            or await date_elem.get_attribute("datetime")
                            or await date_elem.text_content()
                        )
                        if date_str:
                            # Parse the date string
                            from dateutil import parser

                            posted_at = parser.parse(date_str).isoformat()
                            break
                except Exception:
                    continue

            return {
                "url": url,
                "list_url": self.get_archive_url(1),
                "title": title,
                "posted_at": posted_at,
                "collected_at": datetime.now().isoformat(),
                "content": extracted_text,
                "urls": extracted_urls,
            }

        except Exception as e:
            logger.error(f"Error fetching article {url}: {e}")
            return None

    async def crawl(self) -> int:
        """Crawl DataCenter Dynamics articles using Playwright."""
        async with async_playwright() as p:
            # Launch browser with extensive stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-first-run",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-background-networking",
                    "--disable-background-timer-throttling",
                    "--disable-ipc-flooding-protection",
                    "--disable-hang-monitor",
                    "--disable-prompt-on-repost",
                    "--disable-sync",
                    "--disable-translate",
                    "--disable-extensions",
                    "--disable-default-apps",
                    "--disable-component-extensions-with-background-pages",
                ],
            )

            # Create context with realistic browser settings and extra headers
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"macOS"',
                    "Cache-Control": "max-age=0",
                },
            )

            # Add comprehensive stealth measures
            await context.add_init_script(
                """
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });

                // Mock hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });

                // Mock connection
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 100,
                        downlink: 10,
                        saveData: false
                    }),
                });

                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Mock chrome runtime
                window.chrome = {
                    runtime: {},
                };

                // Remove automation indicators
                delete window.navigator.__webdriver_evaluate;
                delete window.navigator.__webdriver_script_function;
                delete window.navigator.__webdriver_script_func;
                delete window.navigator.__webdriver_script_fn;
                delete window.navigator.__fxdriver_evaluate;
                delete window.navigator.__driver_unwrapped;
                delete window.navigator.__webdriver_unwrapped;
                delete window.navigator.__driver_evaluate;
                delete window.navigator.__webdriver_evaluate;
                delete window.navigator.__selenium_evaluate;
                delete window.navigator.__selenium_unwrapped;
                delete window.navigator.__webdriver_script_fn;
                """
            )

            # Create pages for listing and article content
            list_page = await context.new_page()
            article_page = await context.new_page()

            # Enable console logging for debugging
            list_page.on("console", lambda msg: logger.debug(f"List page console: {msg.text}"))
            article_page.on(
                "console", lambda msg: logger.debug(f"Article page console: {msg.text}")
            )

            all_article_urls = set()

            # Crawl archive pages
            with tqdm(total=self.max_pages, desc="Crawling archive pages", unit="page") as pbar:
                for page_num in range(1, self.max_pages + 1):
                    archive_url = self.get_archive_url(page_num)
                    logger.info(f"Crawling archive page {page_num}: {archive_url}")

                    try:
                        # Multiple navigation attempts with different strategies
                        navigation_success = False
                        for attempt in range(3):
                            try:
                                logger.info(f"Navigation attempt {attempt + 1} for page {page_num}")

                                # Clear any existing content
                                await list_page.goto("about:blank")
                                await list_page.wait_for_timeout(1000)

                                # Navigate with progressively more lenient strategies
                                if attempt == 0:
                                    await list_page.goto(
                                        archive_url, wait_until="domcontentloaded", timeout=45000
                                    )
                                elif attempt == 1:
                                    await list_page.goto(
                                        archive_url, wait_until="networkidle", timeout=60000
                                    )
                                else:
                                    # Final attempt - just navigate without waiting
                                    await list_page.goto(archive_url, timeout=60000)
                                    await list_page.wait_for_timeout(10000)  # Fixed wait

                                # Check if we got the page
                                title = await list_page.title()
                                if (
                                    title
                                    and "403" not in title.lower()
                                    and "error" not in title.lower()
                                ):
                                    navigation_success = True
                                    logger.info(
                                        f"Successfully navigated to page {page_num} on attempt {attempt + 1}"
                                    )
                                    break
                                else:
                                    logger.warning(
                                        f"Got blocked/error page on attempt {attempt + 1}: {title}"
                                    )

                            except Exception as nav_error:
                                logger.warning(
                                    f"Navigation attempt {attempt + 1} failed for page {page_num}: {nav_error}"
                                )
                                if attempt < 2:
                                    # Human-like delay between navigation attempts
                                    delay_ms = int(self.rng.uniform(3000, 8000))
                                    await list_page.wait_for_timeout(delay_ms)

                        if not navigation_success:
                            logger.error(f"All navigation attempts failed for page {page_num}")
                            break

                        # Human-like delay for content loading
                        content_delay_ms = int(self.rng.uniform(2000, 6000))
                        await list_page.wait_for_timeout(content_delay_ms)

                        # Extract article links
                        article_links = await self.extract_article_links(list_page)

                        if not article_links:
                            logger.warning(f"No articles found on page {page_num}, stopping")
                            break

                        # Filter out already crawled URLs
                        new_links = [
                            link
                            for link in article_links
                            if link not in self.crawled_urls and link not in all_article_urls
                        ]

                        if not new_links:
                            logger.info(f"No new articles on page {page_num}")
                        else:
                            all_article_urls.update(new_links)
                            logger.info(f"Found {len(new_links)} new articles on page {page_num}")

                        pbar.update(1)

                        # Human-like delay between archive pages
                        page_delay = self.rng.uniform(2, 5)
                        await asyncio.sleep(page_delay)

                    except Exception as e:
                        logger.error(f"Error crawling archive page {page_num}: {e}")
                        continue

            logger.info(f"Found {len(all_article_urls)} total unique articles to crawl")

            # Crawl individual articles
            with tqdm(
                total=len(all_article_urls), desc="Fetching articles", unit="article"
            ) as pbar:
                for url in all_article_urls:
                    # Skip if URL should be ignored
                    if self.url_extractor.should_ignore_url(url):
                        logger.info(f"Skipping ignored URL: {url}")
                        pbar.update(1)
                        continue

                    # Fetch article content
                    article_data = await self.fetch_article_content(article_page, url)

                    if article_data:
                        # Save the article
                        self.save_article(article_data)
                        self.articles_processed += 1

                    pbar.update(1)

                    # Human-like delay between articles to be respectful and avoid rate limiting
                    article_delay = self.rng.uniform(5, 12)  # Random delay between 5-12 seconds
                    await asyncio.sleep(article_delay)

            await browser.close()

            logger.info(f"Crawling completed. Processed {self.articles_processed} new articles")
            logger.info(f"Data saved to {self.output_path}")

            return self.articles_processed

    def save_article(self, article: dict[str, Any]) -> None:
        """Save an article to the output file."""
        # Create backup on first write if file exists
        create_backup = self.articles_processed == 0

        if append_jsonl(article, self.output_path, create_backup):
            if create_backup and Path(f"{self.output_path}.bak").exists():
                logger.info(f"Backup created: {self.output_path}.bak")
        else:
            logger.error(f"Failed to save article to {self.output_path}")


def crawl_datacenter(
    url: Optional[str] = None,
    output_path: str = config.get("crawl.datacenter.output"),
    pages: int = 10,
) -> int:
    """Crawl articles from DataCenter Dynamics website using Playwright to bypass anti-bot protection.

    Args:
        url: Optional specific URL to crawl (ignored for Playwright version)
        output_path: Path to save crawled articles
        pages: Number of archive pages to crawl

    Returns:
        Number of articles processed
    """
    if output_path is None:
        output_path = config.get("crawl.datacenter.output", "data/articles/datacenter.jsonl")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    crawler = DataCenterPlaywrightCrawler(output_path, max_pages=pages)

    # Run the async crawler
    return asyncio.run(crawler.crawl())


if __name__ == "__main__":
    # Test the crawler
    articles_count = crawl_datacenter(pages=2)
    logger.info(f"Crawled {articles_count} articles")

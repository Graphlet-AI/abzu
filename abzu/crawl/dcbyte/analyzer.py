"""Analyzer script to understand DC Byte blog's LOAD MORE functionality using Playwright."""

import asyncio
import json
from typing import Any, Optional

from playwright.async_api import Page, Request, Response, async_playwright

from abzu.logs import get_logger

logger = get_logger(__name__)


class DCByteAnalyzer:
    """Analyzer for DC Byte blog pagination and AJAX requests."""

    def __init__(self) -> None:
        self.ajax_requests: list[dict[str, Any]] = []
        self.initial_posts: list[dict[str, Any]] = []
        self.loaded_posts: list[dict[str, Any]] = []

    async def intercept_request(self, request: Request) -> None:
        """Log network requests to identify AJAX endpoints."""
        # Filter for AJAX/API calls - especially WordPress and Essential Grid
        if any(
            keyword in request.url.lower()
            for keyword in [
                "api",
                "ajax",
                "json",
                "load",
                "more",
                "page",
                "posts",
                "wp-admin",
                "admin-ajax",
                "essential-grid",
            ]
        ):
            logger.info(f"Potential AJAX request: {request.method} {request.url}")
            logger.debug(f"Headers: {request.headers}")

            # Try to get POST data if available
            post_data = None
            try:
                post_data = request.post_data
            except Exception:
                pass

            self.ajax_requests.append(
                {
                    "method": request.method,
                    "url": request.url,
                    "headers": dict(request.headers),
                    "post_data": post_data,
                }
            )

    async def intercept_response(self, response: Response) -> None:
        """Log responses to understand data structure."""
        # Filter for JSON responses that might contain posts
        if "json" in response.headers.get("content-type", ""):
            try:
                data = await response.json()
                logger.info(f"JSON Response from {response.url}")
                logger.debug(f"Response structure: {json.dumps(data, indent=2)[:500]}...")
            except Exception as e:
                logger.debug(f"Could not parse JSON response: {e}")

    async def extract_posts(self, page: Page) -> list[dict[str, Any]]:
        """Extract blog posts from the current page."""
        posts: list[dict[str, Any]] = await page.evaluate(
            """
            () => {
                const posts = [];
                // Look for Essential Grid items specifically for DC Byte
                const gridItems = document.querySelectorAll('.esg-entry-media, .eg-item-skin-1-element-0, [class*="eg-item"]');

                if (gridItems.length > 0) {
                    console.log(`Found ${gridItems.length} grid items`);
                    gridItems.forEach(el => {
                        // Find the parent article element or grid item container
                        const container = el.closest('article') || el.closest('li') || el;

                        // Extract title from various possible locations
                        const titleEl = container.querySelector('.eg-item-skin-1-element-0, .esg-entry-content h3, h3, h2, .title');
                        const title = titleEl?.textContent?.trim();

                        // Extract link
                        const linkEl = container.querySelector('a[href*="/news-blogs/"], a[href*="/blog/"], a');
                        const link = linkEl?.href;

                        // Extract excerpt
                        const excerptEl = container.querySelector('.eg-item-skin-1-element-28, .excerpt, p');
                        const excerpt = excerptEl?.textContent?.trim();

                        // Extract date
                        const dateEl = container.querySelector('.eg-item-skin-1-element-3, time, .date, .meta');
                        const date = dateEl?.textContent?.trim();

                        if (title && link) {
                            posts.push({
                                title: title,
                                link: link,
                                excerpt: excerpt || '',
                                date: date || '',
                                selector: 'essential-grid'
                            });
                        }
                    });
                } else {
                    // Fallback to generic article extraction
                    const articles = document.querySelectorAll('article, .post, .blog-post, .blog-item');
                    articles.forEach(el => {
                        const title = el.querySelector('h1, h2, h3, h4, [class*="title"]')?.textContent?.trim();
                        const link = el.querySelector('a')?.href;
                        const excerpt = el.querySelector('p, [class*="excerpt"], [class*="summary"]')?.textContent?.trim();
                        const date = el.querySelector('time, [class*="date"], [class*="meta"]')?.textContent?.trim();

                        if (title || link) {
                            posts.push({
                                title: title || 'No title',
                                link: link || 'No link',
                                excerpt: excerpt || 'No excerpt',
                                date: date || 'No date',
                                selector: 'article'
                            });
                        }
                    });
                }

                return posts;
            }
            """
        )
        return posts

    async def find_load_more_button(self, page: Page) -> Optional[str]:
        """Find the LOAD MORE button on the page."""
        button_selectors = [
            # DC Byte specific selectors first
            ".eg-ajax-target",  # Essential Grid AJAX target
            ".esg-loadmore",  # Essential Grid load more
            ".eg-item-ajaxcontent",  # Essential Grid AJAX content
            # Generic load more selectors
            'button:has-text("LOAD MORE")',
            'a:has-text("LOAD MORE")',
            ".load-more:visible",
            '[class*="load"][class*="more"]:visible',
            'button:has-text("Load More")',
            'button:has-text("load more")',
            'a:has-text("Load More")',
            '[class*="loadmore"]',
            '[id*="load-more"]',
            '[id*="loadmore"]',
            'button:has-text("Show More")',
            'button:has-text("View More")',
            '[class*="pagination"] button',
            ".more-button",
            ".load-more-button",
        ]

        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    logger.info(f"Found load more button with selector: {selector}")
                    # Get button attributes
                    attrs = await button.evaluate(
                        """
                        (el) => {
                            const attrs = {};
                            for (const attr of el.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            return attrs;
                        }
                        """
                    )
                    logger.debug(f"Button attributes: {attrs}")
                    return selector
            except Exception:
                continue

        logger.warning("Could not find LOAD MORE button")
        return None

    async def analyze(self, url: str = "https://www.dcbyte.com/us/news-blogs/") -> dict[str, Any]:
        """Analyze the DC Byte blog to understand its structure and pagination."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False
            )  # Set to False to see what's happening
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # Set up request/response interception
            page.on("request", self.intercept_request)
            page.on("response", self.intercept_response)

            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)  # Wait for dynamic content

            # Extract initial posts
            logger.info("Extracting initial posts...")
            self.initial_posts = await self.extract_posts(page)
            logger.info(f"Found {len(self.initial_posts)} initial posts")

            if self.initial_posts:
                logger.info(f"Sample post: {self.initial_posts[0]}")

            # Find and click LOAD MORE button
            load_more_selector = await self.find_load_more_button(page)

            if load_more_selector:
                try:
                    # Clear previous AJAX requests
                    self.ajax_requests.clear()

                    logger.info("Scrolling to LOAD MORE button...")
                    # First scroll to the button
                    button = await page.query_selector(load_more_selector)
                    if button:
                        await button.scroll_into_view_if_needed()
                        await page.wait_for_timeout(1000)

                        # Check if it's actually visible and clickable
                        is_visible = await button.is_visible()
                        if is_visible:
                            logger.info("Clicking LOAD MORE button...")
                            await button.click()
                            await page.wait_for_timeout(5000)  # Wait for new content to load
                        else:
                            # Try clicking by evaluating JavaScript
                            logger.info("Button not visible, trying JavaScript click...")
                            await page.evaluate(
                                f"""
                                document.querySelector("{load_more_selector}").click();
                            """
                            )
                            await page.wait_for_timeout(5000)

                    # Extract posts after loading more
                    self.loaded_posts = await self.extract_posts(page)
                    logger.info(f"Found {len(self.loaded_posts)} posts after loading more")

                    new_posts = len(self.loaded_posts) - len(self.initial_posts)
                    logger.info(f"Loaded {new_posts} new posts")

                except Exception as e:
                    logger.error(f"Error clicking LOAD MORE: {e}")

            # Take a screenshot for debugging
            await page.screenshot(path="dcbyte_blog.png")
            logger.info("Screenshot saved to dcbyte_blog.png")

            await browser.close()

            # Analyze results
            analysis = {
                "url": url,
                "initial_posts_count": len(self.initial_posts),
                "loaded_posts_count": len(self.loaded_posts),
                "new_posts_loaded": len(self.loaded_posts) - len(self.initial_posts),
                "load_more_button_found": load_more_selector is not None,
                "load_more_selector": load_more_selector,
                "ajax_requests": self.ajax_requests,
                "sample_posts": self.initial_posts[:3] if self.initial_posts else [],
            }

            return analysis


async def main() -> None:
    """Run the analyzer."""
    analyzer = DCByteAnalyzer()
    results = await analyzer.analyze()

    logger.info("=" * 80)
    logger.info("ANALYSIS RESULTS")
    logger.info("=" * 80)
    logger.info(json.dumps(results, indent=2))

    # Save results to file
    with open("dcbyte_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Analysis saved to dcbyte_analysis.json")

    # Print recommendations
    logger.info("\n" + "=" * 80)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 80)

    if results["ajax_requests"]:
        logger.info("✓ Found AJAX requests that may be used for direct API calls:")
        for req in results["ajax_requests"]:
            logger.info(f"  - {req['method']} {req['url']}")
        logger.info("\nRecommendation: Try direct API calls to these endpoints")
    else:
        logger.info("✗ No clear AJAX requests detected")
        logger.info("\nRecommendation: Use Playwright for browser-based scraping")

    if results["load_more_button_found"]:
        logger.info(f"✓ Load More button found: {results['load_more_selector']}")
    else:
        logger.info("✗ Load More button not found - may need custom selector")


if __name__ == "__main__":
    asyncio.run(main())

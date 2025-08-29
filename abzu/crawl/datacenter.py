"""Crawl articles from DataCenter Dynamics website."""

from typing import Optional

from scrapy.http.response import Response

from abzu.config import config
from abzu.crawl.base import BaseArticleCrawler, crawl_site
from abzu.crawl.datacenter_playwright import crawl_datacenter_playwright


class DataCenterCrawler(BaseArticleCrawler):
    """Legacy Scrapy-based crawler for DataCenter Dynamics articles (blocked by anti-bot protection)."""

    name = "datacenter_crawler"

    def get_article_links(self, response: Response) -> list[str]:
        """Extract article links from the DataCenter Dynamics archive page."""
        # Find all article links using the card structure
        article_links = response.css("article.card a.block-link.headline-link::attr(href)").getall()

        if not article_links:
            # Fallback to a more general selector if the specific one doesn't work
            article_links = response.css("a::attr(href)").getall()
            self._logger.warning(
                f"Using fallback selector for {response.url}. Found {len(article_links)} links."
            )

        return article_links

    def is_article_url(self, url: str, base_url: str) -> bool:
        """Check if a URL is a DataCenter Dynamics article URL."""
        return (
            "datacenterdynamics.com" in base_url
            and "/en/news/" in url
            and not url.endswith("/en/news/")
            and "?page=" not in url
        )


def get_datacenter_archive_urls(pages: int) -> list[str]:
    """Generate DataCenter Dynamics archive URLs."""
    return [f"https://www.datacenterdynamics.com/en/news/?page={n}" for n in range(1, pages + 1)]


def crawl_datacenter(
    url: Optional[str] = None,
    output_path: str = config.get("crawl.datacenter.output"),
    pages: int = 300,
    batch_size: int = 1,
    concurrent_requests: int = 1,
) -> int:
    """Crawl articles from DataCenter Dynamics website using Playwright to bypass anti-bot protection.

    Args:
        url: Optional specific URL to crawl (ignored for Playwright version)
        output_path: Path to save crawled articles
        pages: Number of archive pages to crawl
        batch_size: Number of URLs to process in each batch (ignored for Playwright version)
        concurrent_requests: Number of concurrent requests per spider (ignored for Playwright version)

    Returns:
        Number of articles processed
    """
    # Use Playwright crawler to bypass anti-bot protection
    return crawl_datacenter_playwright(
        output_path=output_path,
        pages=pages,
    )


def main(batch_size: int = 1, concurrent_requests: int = 1):
    """Run crawlers in batches."""
    return crawl_datacenter(batch_size=batch_size, concurrent_requests=concurrent_requests)


if __name__ == "__main__":
    main()

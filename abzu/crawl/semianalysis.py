"""Crawl articles from SemiAnalysis website."""

from typing import Optional

from scrapy.http.response import Response

from abzu.config import config
from abzu.crawl.base import BaseArticleCrawler, crawl_site


class SemiAnalysisCrawler(BaseArticleCrawler):
    """Crawler for SemiAnalysis articles."""

    name = "semianalysis_crawler"

    def get_article_links(self, response: Response) -> list[str]:
        """Extract article links from the SemiAnalysis archive page."""
        # Use a more specific selector for SemiAnalysis articles
        article_links = response.css("article h2 a::attr(href)").getall()
        if not article_links:
            # Fallback to a more general selector
            article_links = response.css("a::attr(href)").getall()
            self._logger.warning(
                f"Using fallback selector for {response.url}. Found {len(article_links)} links."
            )

        return article_links

    def is_article_url(self, url: str, base_url: str) -> bool:
        """Check if a URL is a SemiAnalysis article URL."""
        return "semianalysis.com" in base_url and (
            url.startswith("https://semianalysis.com/20") or "/blog/" in url or "/article/" in url
        )


def get_semianalysis_archive_urls(pages: int) -> list[str]:
    """Generate SemiAnalysis archive URLs."""
    # SemiAnalysis uses reversed order for archive pages
    return list([f"https://semianalysis.com/archives/page/{n}/" for n in range(1, pages + 1)])


def crawl_semianalysis(
    url: Optional[str] = None,
    output_path: str = config.get("crawl.semianalysis.output"),
    pages: int = 24,
    batch_size: int = 10,
) -> int:
    """Crawl articles from SemiAnalysis website in batch mode.

    Args:
        url: Optional specific URL to crawl
        output_path: Path to save crawled articles
        pages: Number of archive pages to crawl
        batch_size: Number of concurrent requests (default: 10)

    Returns:
        0 on success, 1 on failure
    """
    return crawl_site(
        crawler_class=SemiAnalysisCrawler,
        get_archive_urls_func=get_semianalysis_archive_urls,
        output_path=output_path,
        url=url,
        pages=pages,
        batch_size=batch_size,
        concurrent_requests=batch_size,  # Use batch_size for concurrent requests
    )


def main(batch_size: int = 10):
    """Run crawlers in batches."""
    return crawl_semianalysis(batch_size=batch_size)


if __name__ == "__main__":
    main()


# Keep backward compatibility
ArticleCrawler = SemiAnalysisCrawler
run_batch_crawl = crawl_semianalysis

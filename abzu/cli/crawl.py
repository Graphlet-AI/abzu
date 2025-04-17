"""Crawl articles from the web for processing."""

import logging
import os
from typing import Optional

from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from abzu.crawl import DEFAULT_PATH, ArticleCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def crawl_main(url: Optional[str] = None, output_path: str = DEFAULT_PATH, pages: int = 24) -> int:
    """Crawl articles from specified URLs."""
    try:
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        configure_logging()
        settings = get_project_settings()

        # Set crawler settings
        settings.set("CONCURRENT_REQUESTS", 1)
        settings.set("DOWNLOAD_DELAY", 0.5)

        runner = CrawlerRunner(settings)

        # If a specific URL is provided, crawl only that URL
        if url:
            logger.info(f"Crawling URL: {url}")

            @defer.inlineCallbacks
            def crawl_single():
                yield runner.crawl(
                    ArticleCrawler,
                    archive_url=url,
                    output_path=output_path,
                )
                reactor.stop()

            crawl_single()
        else:
            # Otherwise, crawl the archive pages
            logger.info(f"Crawling {pages} archive pages")
            archive_urls = reversed(
                [f"https://semianalysis.com/archives/page/{n}/" for n in range(1, pages + 1)]
            )

            @defer.inlineCallbacks
            def crawl_archives():
                for archive_url in archive_urls:
                    logger.info(f"Crawling archive page: {archive_url}")
                    yield runner.crawl(
                        ArticleCrawler,
                        archive_url=archive_url,
                        output_path=output_path,
                    )
                reactor.stop()

            crawl_archives()

        # Start the reactor
        reactor.run()
        logger.info(f"Crawling complete, data saved to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        logger.exception("Full exception details:")
        return 1


def main() -> int:
    """Command line interface for crawler."""
    return crawl_main()


if __name__ == "__main__":
    import sys

    sys.exit(main())

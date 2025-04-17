"""Crawl articles from the web for processing."""

import logging
import os
import time
from typing import Optional

from twisted.internet import defer, reactor

from abzu.crawl import DEFAULT_PATH, run_batch_crawl

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def crawl_main(
    url: Optional[str] = None,
    output_path: str = DEFAULT_PATH,
    pages: int = 24,
    batch_size: int = 5,
    concurrent_requests: int = 5,
) -> int:
    """Crawl articles from specified URLs in batch mode."""
    try:
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # If a specific URL is provided, crawl only that URL in a single batch
        if url:
            logger.info(f"Crawling URL: {url}")
            urls = [url]
        else:
            # Otherwise, get the archive pages
            logger.info(f"Preparing to crawl {pages} archive pages in batches of {batch_size}")
            urls = list(
                reversed(
                    [f"https://semianalysis.com/archives/page/{n}/" for n in range(1, pages + 1)]
                )
            )

        total_urls = len(urls)

        # Process URLs in batches
        batches = [urls[i : i + batch_size] for i in range(0, total_urls, batch_size)]
        logger.info(
            f"Processing {total_urls} URLs in {len(batches)} batches of up to {batch_size} URLs each"
        )

        @defer.inlineCallbacks
        def process_batches():
            start_time = time.time()
            for i, batch in enumerate(batches):
                logger.info(f"Starting batch {i + 1}/{len(batches)} with {len(batch)} URLs")
                # Process this batch
                yield run_batch_crawl(batch, output_path, concurrent_requests)
                logger.info(f"Completed batch {i + 1}/{len(batches)}")

            # All done!
            elapsed = time.time() - start_time
            logger.info(f"All batches completed in {elapsed:.2f} seconds")
            logger.info(f"Data saved to {output_path}")
            reactor.stop()

        # Start the process
        process_batches()
        # Blocks until reactor.stop() is called
        reactor.run()

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

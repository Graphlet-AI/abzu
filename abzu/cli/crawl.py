"""Crawl articles from the web for processing."""

import logging
import os
import time
from typing import Any, Optional, cast

from tqdm import tqdm
from twisted.internet import defer
from twisted.internet import reactor as twisted_reactor

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

        # Create progress bar for total pages to crawl
        progress = tqdm(
            total=total_urls,
            desc="Crawling pages",
            unit="page",
            position=0,
            leave=True,
            colour="green"
        )

        # Process URLs in batches
        batches = [urls[i : i + batch_size] for i in range(0, total_urls, batch_size)]
        logger.info(
            f"Processing {total_urls} URLs in {len(batches)} batches of up to {batch_size} URLs each"
        )

        @defer.inlineCallbacks
        def process_batches():
            start_time = time.time()
            for i, batch in enumerate(batches):
                batch_desc = f"Batch {i + 1}/{len(batches)}"
                progress.set_description(batch_desc)
                # Process this batch with our progress bar
                yield run_batch_crawl(
                    batch,
                    output_path,
                    concurrent_requests,
                    progress_bar=progress
                )

            # All done!
            elapsed = time.time() - start_time
            progress.close()
            logger.info(f"All batches completed in {elapsed:.2f} seconds")
            logger.info(f"Data saved to {output_path}")
            twisted_reactor.stop()

        # Start the process
        process_batches()
        # Blocks until twisted_reactor.stop() is called
        # Add cast to Any to help mypy understand this method exists
        cast(Any, twisted_reactor).run()

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

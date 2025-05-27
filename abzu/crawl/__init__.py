"""Crawl articles from the web for processing."""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional, cast

import dateutil.parser
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http.response import Response
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from tqdm import tqdm
from twisted.internet import asyncioreactor, defer

# Install the AsyncIO reactor before importing or using the reactor
asyncioreactor.install()
from twisted.internet import reactor  # noqa: E402

from abzu.utils import append_jsonl, build_crawled_url_index  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_PATH = "data/semianalysis.jsonl"


class ArticleCrawler(scrapy.Spider):
    name = "article_crawler"

    # Class level attributes for tracking
    _backup_done = False
    _total_articles_processed = 0
    _skipped_articles = 0

    custom_settings = {
        "COOKIES_ENABLED": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "DOWNLOAD_TIMEOUT": 10,
        "DOWNLOAD_DELAY": 0.5,  # Enforce a minimum delay of 0.5 seconds between requests
        "RANDOMIZE_DOWNLOAD_DELAY": False,  # Don't randomize the delay
        "CONCURRENT_REQUESTS": 1,  # Only one request at a time
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,  # Only one request per domain at a time
    }

    def __init__(
        self,
        archive_url: str,
        output_path: str = DEFAULT_PATH,
        crawled_urls: Optional[set[str]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_urls: list[str] = [archive_url]
        self.output_file: Path = Path(output_path)
        self.start_time = datetime.now()
        self.articles_processed = 0
        # Set of URLs that have already been crawled
        self.crawled_urls = crawled_urls if crawled_urls is not None else set()

    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the archive page and follow links to individual articles."""
        # Print the archive page being crawled
        logger.info(f"Parsing archive page: {response.url}")

        # Log the response status to help with debugging
        logger.info(f"Response status: {response.status}")

        # Find all article links - adjust selector based on actual HTML structure
        # Use a more specific selector for SemiAnalysis articles
        if "semianalysis.com" in response.url:
            article_links = response.css("article h2 a::attr(href)").getall()
            if not article_links:
                # Fallback to a more general selector
                article_links = response.css("a::attr(href)").getall()
                logger.warning(
                    f"Using fallback selector for {response.url}. Found {len(article_links)} links."
                )
        else:
            article_links = response.css("a::attr(href)").getall()

        found_articles = 0
        new_articles = 0
        skipped_articles = 0

        # Log the number of links found
        logger.info(f"Found {len(article_links)} total links on page {response.url}")

        for link in article_links:
            absolute_url = response.urljoin(link)

            # Check if the URL matches the pattern for a SemiAnalysis article
            is_article = False
            if "semianalysis.com" in response.url and (
                absolute_url.startswith("https://semianalysis.com/20")
                or "/blog/" in absolute_url
                or "/article/" in absolute_url
            ):
                is_article = True

            if is_article:
                found_articles += 1
                # Check if URL has already been crawled
                if absolute_url in self.crawled_urls:
                    skipped_articles += 1
                    self.__class__._skipped_articles += 1
                    logger.info(f"Skipping already crawled URL: {absolute_url}")
                else:
                    new_articles += 1
                    logger.info(f"Queuing new article URL: {absolute_url}")
                    yield scrapy.Request(
                        absolute_url, callback=self.parse_article, errback=self.handle_error
                    )

        logger.info(
            f"Found {found_articles} articles on page: {response.url} "
            f"(new: {new_articles}, skipped: {skipped_articles})"
        )

    def handle_error(self, failure):
        """Handle request failures."""
        logger.error(f"Request failed: {failure.request.url}")
        logger.error(f"Error: {failure.value}")
        return None

    def parse_article(self, response: Response) -> None:
        """Parse and save individual article content."""
        # Log the URL being crawled
        logger.info(f"Crawling article: {response.url}")

        # Log the response status for debugging
        logger.info(f"Article response status: {response.status}")

        # Extract the title
        title = response.css("title::text").get() or "untitled"
        logger.info(f"Article title: {title}")

        # Try different selectors for content based on the site structure
        if "semianalysis.com" in response.url:
            # First try the main content selector
            text_fragments = response.css("div.entry-content *::text, article *::text").getall()
            if not text_fragments:
                # Fallback to a more general selector
                text_fragments = response.css("article *::text, .post-content *::text").getall()
                if not text_fragments:
                    # Last resort selector
                    text_fragments = response.css("body *::text").getall()
                    logger.warning(f"Using last resort selector for {response.url}")
        else:
            text_fragments = response.css("div.entry-content *::text").getall()

        # Log the number of text fragments found
        logger.info(f"Found {len(text_fragments)} text fragments in the article")

        # Try various selectors for the publication date
        posted_at_str = (
            response.css('meta[property="article:published_time"]::attr(content)').get()
            or response.css("time::attr(datetime)").get()
            or response.css('meta[name="pubdate"]::attr(content)').get()
        )

        if posted_at_str:
            try:
                posted_at = dateutil.parser.parse(posted_at_str)
                logger.info(f"Extracted publication date: {posted_at}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse posted_at for {response.url}: {e}")
                posted_at = datetime.now()
        else:
            logger.warning(f"No posted_at metadata found for {response.url}")
            posted_at = datetime.now()

        # Join the text fragments into a single content string
        content: str = " ".join(text_fragments).strip()

        # Log a snippet of the content for debugging
        content_preview = content[:200] + "..." if len(content) > 200 else content
        logger.info(f"Content preview: {content_preview}")

        # Save the article
        self.save(
            {
                "url": response.url,
                "list_url": self.start_urls[0],
                "title": title,
                "posted_at": posted_at.isoformat(),
                "collected_at": datetime.now().isoformat(),
                "content": content,
            }
        )

    def save(self, article) -> None:
        """Save all collected articles to the output file."""
        # First article will create a backup if file exists
        # Subsequent articles will not (more efficient for large crawls)
        static_backup_done = getattr(self.__class__, "_backup_done", False)
        create_backup = not static_backup_done

        if append_jsonl(article, self.output_file, create_backup):
            if create_backup and Path(f"{self.output_file}.bak").exists():
                self.logger.info(f"Backup created: {self.output_file}.bak")
                # Set flag so we don't create multiple backups during the crawl
                self.__class__._backup_done = True

            # Update stats
            self.articles_processed += 1
            self.__class__._total_articles_processed += 1

            # Update the progress bar if it exists
            # Access the global progress bar without re-declaring it
            if _progress_bar:
                _progress_bar.set_postfix(
                    articles=self.__class__._total_articles_processed, refresh=True
                )

            # Log progress occasionally
            if self.articles_processed % 10 == 0:
                elapsed = datetime.now() - self.start_time
                rate = self.articles_processed / max(elapsed.total_seconds(), 1)
                self.logger.info(
                    f"Crawler progress: {self.articles_processed} articles from {self.start_urls[0]} "
                    f"(rate: {rate:.2f} articles/sec)"
                )
        else:
            self.logger.error(f"Failed to save article to {self.output_file}")

    def closed(self, reason):
        """Called when the crawler is closed."""
        elapsed = datetime.now() - self.start_time
        self.logger.info(
            f"Crawler finished: processed {self.articles_processed} articles from {self.start_urls[0]}, "
            f"skipped {self.__class__._skipped_articles} already crawled articles, "
            f"in {elapsed.total_seconds():.2f} seconds"
        )


# Global progress bar
_progress_bar: Optional[tqdm] = None


# To run batch crawls with async
def run_batch_crawl(
    urls: list[str],
    output_path: str = DEFAULT_PATH,
    concurrent_requests: int = 1,
    progress_bar: Optional[tqdm] = None,
    crawled_urls: Optional[set[str]] = None,
):
    """Run crawlers sequentially with configurable concurrency.

    Args:
        urls: List of archive pages to crawl.
        output_path: File to write crawled articles.
        concurrent_requests: Number of concurrent requests per spider.
        progress_bar: Progress bar instance for reporting progress.
        crawled_urls: Optional set of URLs already processed.
    """
    global _progress_bar
    _progress_bar = progress_bar

    # If crawled_urls is None, build it from the output file
    if crawled_urls is None:
        crawled_urls = build_crawled_url_index(output_path)
        print(f"Built index of {len(crawled_urls)} previously crawled URLs")

    configure_logging()
    settings = get_project_settings()
    # Configure concurrency for the spider
    settings.set("CONCURRENT_REQUESTS", concurrent_requests)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", concurrent_requests)
    settings.set("DOWNLOAD_DELAY", 0.5)  # Minimum delay between requests
    settings.set("LOG_LEVEL", "INFO")

    # Make sure we're using the AsyncIO reactor that we installed
    settings.set("TWISTED_REACTOR", "twisted.internet.asyncioreactor.AsyncioSelectorReactor")

    runner = CrawlerRunner(settings)

    # Define a function to process URLs one at a time
    @defer.inlineCallbacks
    def process_sequentially(url_list):
        for url in url_list:
            print(f"Starting crawl for {url}")
            # Process one URL at a time with the crawled_urls set
            yield runner.crawl(
                ArticleCrawler, archive_url=url, output_path=output_path, crawled_urls=crawled_urls
            )
            # Update progress bar after each URL is processed
            if _progress_bar:
                _progress_bar.update(1)
            # Add a small delay between spiders to ensure complete separation
            time.sleep(0.5)

    # Return a deferred that fires when all URLs are processed sequentially
    return process_sequentially(urls)


def crawl_semianalysis(
    url: Optional[str] = None,
    output_path: str = DEFAULT_PATH,
    pages: int = 24,
    batch_size: int = 1,
    concurrent_requests: int = 1,
) -> int:
    """Crawl articles from SemiAnalysis website in batch mode.

    Args:
        url: Optional specific URL to crawl
        output_path: Path to save crawled articles
        pages: Number of archive pages to crawl
        batch_size: Number of URLs to process in each batch
        concurrent_requests: Number of concurrent requests per spider

    Returns:
        0 on success, 1 on failure
    """
    # Track if we've already installed the reactor
    reactor_running = False
    progress = None

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
            colour="green",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} pages [ETA: {remaining}]",
        )

        # Build an index of already crawled URLs
        logger.info(f"Building index of previously crawled URLs from {output_path}")
        crawled_urls = build_crawled_url_index(output_path)
        logger.info(f"Found {len(crawled_urls)} previously crawled URLs")

        # Process URLs in batches
        batches = [urls[i : i + batch_size] for i in range(0, total_urls, batch_size)]
        logger.info(
            f"Processing {total_urls} URLs in {len(batches)} batches of up to {batch_size} URLs each"
        )

        @defer.inlineCallbacks
        def process_batches():
            try:
                start_time = time.time()
                for i, batch in enumerate(batches):
                    batch_desc = f"Batch {i + 1}/{len(batches)}"
                    if progress:
                        progress.set_description(batch_desc)
                    # Process this batch with our progress bar and crawled URLs index
                    yield run_batch_crawl(
                        batch,
                        output_path,
                        concurrent_requests,
                        progress_bar=progress,
                        crawled_urls=crawled_urls,
                    )

                # All done!
                elapsed = time.time() - start_time
                if progress:
                    progress.close()
                logger.info(f"All batches completed in {elapsed:.2f} seconds")
                logger.info(f"Data saved to {output_path}")
            except Exception as e:
                logger.error(f"Error during batch processing: {e}")
                logger.exception("Full exception details:")
            finally:
                # Always stop the reactor when we're done, even if there was an error
                # Type annotations for reactor should be cast to Any
                # to address the mypy error about missing attributes
                if cast(Any, reactor).running:
                    cast(Any, reactor).stop()

        # Set up signal handlers to gracefully exit on interrupt
        import signal

        def signal_handler(sig, frame):
            logger.info("Received interrupt signal, shutting down gracefully...")
            if progress:
                progress.close()
            if cast(Any, reactor).running:
                cast(Any, reactor).stop()

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Set up a timeout to prevent indefinite hanging
        def timeout_handler():
            logger.warning("Crawler timed out after 300 seconds, shutting down...")
            if progress:
                progress.close()
            if cast(Any, reactor).running:
                cast(Any, reactor).stop()

        # Schedule the timeout (5 minutes)
        cast(Any, reactor).callLater(300, timeout_handler)

        # Start the process
        process_batches()

        # Blocks until reactor.stop() is called
        reactor_running = True
        cast(Any, reactor).run()

        return 0
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
        logger.exception("Full exception details:")
        return 1
    finally:
        # Final cleanup
        if progress:
            progress.close()

        # Make absolutely sure the reactor is stopped
        if reactor_running and cast(Any, reactor).running:
            try:
                cast(Any, reactor).stop()
            except Exception:
                pass


def main(batch_size: int = 1, concurrent_requests: int = 1):
    """Run crawlers in batches."""
    return crawl_semianalysis(batch_size=batch_size, concurrent_requests=concurrent_requests)


if __name__ == "__main__":
    main()

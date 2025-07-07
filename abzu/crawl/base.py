"""Base crawler class for article extraction from websites."""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional, cast

# Install the AsyncIO reactor before any other twisted imports
from twisted.internet import asyncioreactor
from twisted.internet.error import ReactorAlreadyInstalledError

try:
    asyncioreactor.install()
except ReactorAlreadyInstalledError:
    # Reactor already installed
    pass

import dateutil.parser
import scrapy
import scrapy.utils.log
from scrapy.crawler import CrawlerRunner
from scrapy.http.response import Response
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from tqdm import tqdm
from twisted.internet import defer, reactor

from abzu.config import config
from abzu.html_extractor import HTMLExtractor
from abzu.logs import get_logger
from abzu.url_extractor import URLExtractor
from abzu.utils import append_jsonl, build_crawled_url_index

# Configure logging levels to reduce verbosity
logging.getLogger("abzu.url_extractor").setLevel(logging.WARNING)
logging.getLogger("abzu.html_extractor").setLevel(logging.WARNING)
logging.getLogger("abzu.utils").setLevel(logging.WARNING)

# Suppress verbose Scrapy logs
logging.getLogger("scrapy.middleware").setLevel(logging.WARNING)
logging.getLogger("scrapy.extensions").setLevel(logging.WARNING)
logging.getLogger("scrapy.crawler").setLevel(logging.WARNING)
logging.getLogger("scrapy.addons").setLevel(logging.WARNING)


class BaseArticleCrawler(scrapy.Spider, ABC):
    """Base class for article crawlers with common functionality."""

    # Class level attributes for tracking
    _backup_done = False
    _total_articles_processed = 0
    _skipped_articles = 0
    _custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    def __init__(
        self,
        archive_url: str,
        output_path: str,
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
        # Initialize HTML extractor
        self.html_extractor = HTMLExtractor()
        # Initialize URL extractor
        self.url_extractor = URLExtractor()
        # Get logger instance - use Scrapy's logger to avoid duplicates
        self._logger = get_logger(self.__class__.__name__)

        # Load custom settings from config
        spider_config = config.get("crawl.spider.config")
        self.custom_settings = spider_config

    @abstractmethod
    def get_article_links(self, response: Response) -> list[str]:
        """Extract article links from the archive page.

        Args:
            response: The scrapy response object

        Returns:
            List of article URLs found on the page
        """
        pass

    @abstractmethod
    def is_article_url(self, url: str, base_url: str) -> bool:
        """Check if a URL is an article URL for this site.

        Args:
            url: The URL to check
            base_url: The base URL of the site

        Returns:
            True if this is an article URL, False otherwise
        """
        pass

    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the archive page and follow links to individual articles."""
        # Print the archive page being crawled
        self._logger.info(f"Parsing archive page: {response.url}")

        # Log the response status to help with debugging
        self._logger.debug(f"Response status: {response.status}")

        # Get article links using site-specific logic
        article_links = self.get_article_links(response)

        found_articles = 0
        new_articles = 0
        skipped_articles = 0

        # Log the number of links found
        self._logger.info(f"Found {len(article_links)} total links on page {response.url}")

        for link in article_links:
            absolute_url = response.urljoin(link)

            # Check if the URL matches the pattern for an article
            if self.is_article_url(absolute_url, response.url):
                found_articles += 1
                # Check if URL has already been crawled
                if absolute_url in self.crawled_urls:
                    skipped_articles += 1
                    self.__class__._skipped_articles += 1
                    self._logger.info(f"Skipping already crawled URL: {absolute_url}")
                # Check if URL should be ignored
                elif self.url_extractor.should_ignore_url(absolute_url):
                    skipped_articles += 1
                    self.__class__._skipped_articles += 1
                    self._logger.info(f"Skipping ignored URL: {absolute_url}")
                else:
                    new_articles += 1
                    self._logger.info(f"Queuing new article URL: {absolute_url}")
                    yield scrapy.Request(
                        absolute_url,
                        callback=self.parse_article,
                        errback=self.handle_error,
                        headers={
                            "Referer": "https://www.google.com/",
                            "Cache-Control": "max-age=0",
                        },
                    )

        self._logger.info(
            f"Found {found_articles} articles on page: {response.url} "
            f"(new: {new_articles}, skipped: {skipped_articles})"
        )

    def handle_error(self, failure):
        """Handle request failures."""
        self._logger.error(f"Request failed: {failure.request.url}")
        self._logger.error(f"Error: {failure.value}")
        return None

    def parse_article(self, response: Response) -> None:
        """Parse and save individual article content."""
        # Log the URL being crawled
        self._logger.info(f"Crawling article: {response.url}")

        # Log the response status for debugging
        self._logger.debug(f"Article response status: {response.status}")

        # Extract the title
        title = response.css("title::text").get() or "untitled"
        self._logger.debug(f"Article title: {title}")

        # Try various selectors for the publication date
        posted_at_str = (
            response.css('meta[property="article:published_time"]::attr(content)').get()
            or response.css("time::attr(datetime)").get()
            or response.css('meta[name="pubdate"]::attr(content)').get()
        )

        if posted_at_str:
            try:
                posted_at = dateutil.parser.parse(posted_at_str)
                self._logger.debug(f"Extracted publication date: {posted_at}")
            except (ValueError, TypeError) as e:
                self._logger.warning(f"Failed to parse posted_at for {response.url}: {e}")
                posted_at = None
        else:
            self._logger.warning(f"No posted_at metadata found for {response.url}")
            posted_at = None

        # Get the full HTML content
        html_content = response.text

        # Extract URLs from HTML
        extracted_urls = self.url_extractor.extract_urls_from_html(html_content)
        self._logger.debug(f"Extracted {len(extracted_urls)} URLs from article")

        # Extract text using HTMLExtractor
        extracted_text = self.html_extractor.extract(html_content)

        # Log the extraction result
        original_size = len(html_content)
        extracted_size = len(extracted_text)
        reduction_pct = (
            ((original_size - extracted_size) / original_size * 100) if original_size > 0 else 0
        )
        self._logger.debug(
            f"Extracted text from HTML: {original_size:,} → {extracted_size:,} chars "
            f"({reduction_pct:.1f}% reduction)"
        )

        # Log a snippet of the content for debugging
        content_preview = (
            extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
        )
        self._logger.debug(f"Content preview: {content_preview}")

        # Save the article with extracted text and URLs
        self.save(
            {
                "url": response.url,
                "list_url": self.start_urls[0],
                "title": title,
                "posted_at": posted_at.isoformat() if posted_at else None,
                "collected_at": datetime.now().isoformat(),
                "content": extracted_text,
                "urls": extracted_urls,
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
                self._logger.info(f"Backup created: {self.output_file}.bak")
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
                self._logger.info(
                    f"Crawler progress: {self.articles_processed} articles from {self.start_urls[0]} "
                    f"(rate: {rate:.2f} articles/sec)"
                )
        else:
            self._logger.error(f"Failed to save article to {self.output_file}")

    def closed(self, reason):
        """Called when the crawler is closed."""
        elapsed = datetime.now() - self.start_time
        self._logger.info(
            f"Crawler finished: processed {self.articles_processed} articles from {self.start_urls[0]}, "
            f"skipped {self.__class__._skipped_articles} already crawled articles, "
            f"in {elapsed.total_seconds():.2f} seconds"
        )


# Global progress bar
_progress_bar: Optional[tqdm] = None


def run_batch_crawl(
    crawler_class: type[BaseArticleCrawler],
    urls: list[str],
    output_path: str,
    concurrent_requests: int = 1,
    progress_bar: Optional[tqdm] = None,
    crawled_urls: Optional[set[str]] = None,
):
    """Run crawlers sequentially with configurable concurrency.

    Args:
        crawler_class: The crawler class to use
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

    # Configure Scrapy logging to avoid duplicates
    configure_logging(
        {
            "LOG_ENABLED": True,
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT": "%(levelname)s: %(message)s",
        }
    )

    settings = get_project_settings()

    # Load spider config from config.yml
    spider_config = config.get("crawl.spider.config")
    for key, value in spider_config.items():
        settings.set(key, value)

    # Configure concurrency for the spider
    settings.set("CONCURRENT_REQUESTS", concurrent_requests)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", concurrent_requests)

    # Disable verbose startup logs
    settings.set("LOG_STDOUT", False)

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
                crawler_class, archive_url=url, output_path=output_path, crawled_urls=crawled_urls
            )
            # Update progress bar after each URL is processed
            if _progress_bar:
                _progress_bar.update(1)
            # Add a small delay between spiders to ensure complete separation
            time.sleep(0.7)

    # Return a deferred that fires when all URLs are processed sequentially
    return process_sequentially(urls)


def crawl_site(
    crawler_class: type[BaseArticleCrawler],
    get_archive_urls_func,
    output_path: str,
    url: Optional[str] = None,
    pages: int = 10,
    batch_size: int = 1,
    concurrent_requests: int = 1,
) -> int:
    """Generic site crawler function.

    Args:
        crawler_class: The crawler class to use
        get_archive_urls_func: Function to generate archive URLs for the site
        output_path: Path to save crawled articles
        url: Optional specific URL to crawl
        pages: Number of archive pages to crawl
        batch_size: Number of URLs to process in each batch
        concurrent_requests: Number of concurrent requests per spider

    Returns:
        0 on success, 1 on failure
    """
    import os
    import signal

    # Track if we've already installed the reactor
    reactor_running = False
    progress = None

    logger = get_logger(__name__)

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
            urls = get_archive_urls_func(pages)

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
        logger.debug(f"Building index of previously crawled URLs from {output_path}")
        crawled_urls = build_crawled_url_index(output_path)
        logger.info(f"Found {len(crawled_urls)} previously crawled URLs")

        # Process URLs in batches
        batches = [urls[i : i + batch_size] for i in range(0, total_urls, batch_size)]
        logger.debug(
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
                        crawler_class,
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
                logger.info(
                    "Total articles processed: %d", BaseArticleCrawler._total_articles_processed
                )
            except Exception as e:
                logger.error(f"Error during batch processing: {e}")
                logger.exception("Full exception details:")
            finally:
                # Always stop the reactor when we're done, even if there was an error
                # Type annotations for reactor should be cast to Any
                # to address the mypy error about missing attributes
                logger.info("Stopping reactor...")
                if cast(Any, reactor).running:
                    cast(Any, reactor).stop()
                    logger.info("Reactor stopped")

        # Set up signal handlers to gracefully exit on interrupt
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
        timeout_id = cast(Any, reactor).callLater(300, timeout_handler)

        # Start the process
        d = process_batches()

        # Add a callback to cancel the timeout when done
        def cancel_timeout(result):
            if timeout_id.active():
                timeout_id.cancel()
            return result

        d.addBoth(cancel_timeout)

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

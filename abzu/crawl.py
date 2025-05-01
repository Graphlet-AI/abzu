import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List, Optional, Set, cast

import dateutil.parser
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http.response import Response
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from tqdm import tqdm
from twisted.internet import defer, reactor

from abzu.utils import append_jsonl, build_crawled_url_index

DEFAULT_PATH = "data/articles.jsonl"


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
        crawled_urls: Optional[Set[str]] = None,
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
        print(f"Parsing archive page: {response.url}")
        # Find all article links - adjust selector based on actual HTML structure
        article_links = response.css("a::attr(href)").getall()
        found_articles = 0
        new_articles = 0
        skipped_articles = 0
        for link in article_links:
            absolute_url = response.urljoin(link)
            if absolute_url.startswith("https://semianalysis.com/20"):
                found_articles += 1
                # Check if URL has already been crawled
                if absolute_url in self.crawled_urls:
                    skipped_articles += 1
                    self.__class__._skipped_articles += 1
                    print(f"Skipping already crawled URL: {absolute_url}")
                else:
                    new_articles += 1
                    yield scrapy.Request(absolute_url, callback=self.parse_article)

        print(
            f"Found {found_articles} articles on page: {response.url} "
            f"(new: {new_articles}, skipped: {skipped_articles})"
        )

    def parse_article(self, response: Response) -> None:
        """Parse and save individual article content."""
        # Print the URL being crawled
        print(f"Crawling article: {response.url}")
        title = response.css("title::text").get() or "untitled"
        text_fragments: list[str] = response.css("div.entry-content *::text").getall()
        posted_at: datetime = dateutil.parser.parse(
            str(response.css('meta[property="article:published_time"]::attr(content)').get())
        )
        content: str = " ".join(text_fragments).strip()
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
    urls: List[str],
    output_path: str = DEFAULT_PATH,
    concurrent_requests: int = 1,
    progress_bar: Optional[tqdm] = None,
    crawled_urls: Optional[Set[str]] = None,
):
    """Run crawlers sequentially, one at a time."""
    global _progress_bar
    _progress_bar = progress_bar

    # If crawled_urls is None, build it from the output file
    if crawled_urls is None:
        crawled_urls = build_crawled_url_index(output_path)
        print(f"Built index of {len(crawled_urls)} previously crawled URLs")

    configure_logging()
    settings = get_project_settings()
    # Set settings to enforce sequential processing
    settings.set("CONCURRENT_REQUESTS", 1)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", 1)
    settings.set("DOWNLOAD_DELAY", 0.5)  # Minimum delay between requests
    settings.set("LOG_LEVEL", "INFO")

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


def main(batch_size: int = 1, concurrent_requests: int = 1):
    """Run crawlers in batches."""
    configure_logging()

    # Get all archive URLs
    archive_urls = list(
        reversed([f"https://semianalysis.com/archives/page/{n}/" for n in range(1, 24)])
    )
    total_urls = len(archive_urls)

    # Process URLs in batches
    batches = [archive_urls[i : i + batch_size] for i in range(0, total_urls, batch_size)]
    print(f"Processing {total_urls} URLs in {len(batches)} batches of up to {batch_size} URLs each")

    @defer.inlineCallbacks
    def process_batches():
        start_time = datetime.now()
        for i, batch in enumerate(batches):
            print(f"Starting batch {i + 1}/{len(batches)} with {len(batch)} URLs")
            # Process this batch
            yield run_batch_crawl(batch, DEFAULT_PATH, concurrent_requests)
            print(f"Completed batch {i + 1}/{len(batches)}")

        # All done!
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"All batches completed in {elapsed:.2f} seconds")
        reactor.stop()

    # Start the process
    process_batches()
    # Add cast to Any to help mypy understand this method exists
    cast(Any, reactor).run()  # Blocks until reactor.stop() is called.


if __name__ == "__main__":
    main()

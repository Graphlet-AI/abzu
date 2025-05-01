import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List, Optional, cast

import dateutil.parser
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http.response import Response
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from tqdm import tqdm
from twisted.internet import defer, reactor

from abzu.utils import append_jsonl

DEFAULT_PATH = "data/articles.jsonl"


class ArticleCrawler(scrapy.Spider):
    name = "article_crawler"

    # Class level attributes for tracking
    _backup_done = False
    _total_articles_processed = 0

    custom_settings = {
        "COOKIES_ENABLED": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "DOWNLOAD_TIMEOUT": 10,
    }

    def __init__(
        self,
        archive_url: str,
        output_path: str = DEFAULT_PATH,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.start_urls: list[str] = [archive_url]
        self.output_file: Path = Path(output_path)
        self.start_time = datetime.now()
        self.articles_processed = 0

    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse the archive page and follow links to individual articles."""
        # Find all article links - adjust selector based on actual HTML structure
        article_links = response.css("a::attr(href)").getall()
        for link in article_links:
            absolute_url = response.urljoin(link)
            if absolute_url.startswith("https://semianalysis.com/20"):
                yield scrapy.Request(absolute_url, callback=self.parse_article)

    def parse_article(self, response: Response) -> None:
        """Parse and save individual article content."""
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
            f"Crawler finished: processed {self.articles_processed} articles from {self.start_urls[0]} "
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
):
    """Run crawlers in batches concurrently."""
    global _progress_bar
    _progress_bar = progress_bar

    configure_logging()
    settings = get_project_settings()
    # Set concurrency and other settings
    settings.set("CONCURRENT_REQUESTS", concurrent_requests)
    settings.set("CONCURRENT_REQUESTS_PER_DOMAIN", concurrent_requests)
    settings.set("DOWNLOAD_DELAY", 0.2)
    settings.set("LOG_LEVEL", "INFO")

    runner = CrawlerRunner(settings)

    # Create a cooperative deferred list for our batch
    deferreds = []
    for url in urls:
        print(f"Starting crawl for {url}")
        # Schedule crawler for each URL
        deferred = runner.crawl(ArticleCrawler, archive_url=url, output_path=output_path)
        deferreds.append(deferred)
        # Update progress bar for each URL submitted
        if _progress_bar:
            _progress_bar.update(1)

    # Return a single deferred that fires when all crawlers complete
    return defer.DeferredList(deferreds)


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

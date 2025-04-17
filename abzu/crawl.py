from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import dateutil.parser
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http.response import Response
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

from abzu.utils import append_jsonl

DEFAULT_PATH = "data/articles.jsonl"


class ArticleCrawler(scrapy.Spider):
    name = "article_crawler"

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
        static_backup_done = getattr(self, "_backup_done", False)
        create_backup = not static_backup_done

        if append_jsonl(article, self.output_file, create_backup):
            if create_backup and Path(f"{self.output_file}.bak").exists():
                self.logger.info(f"Backup created: {self.output_file}.bak")
                # Set flag so we don't create multiple backups during the crawl
                self.__class__._backup_done = True
        else:
            self.logger.error(f"Failed to save article to {self.output_file}")


# To run sequential crawls without restarting the reactor:
def main():
    configure_logging()
    settings = get_project_settings()
    # Set low concurrency and add a download delay
    settings.set("CONCURRENT_REQUESTS", 1)
    settings.set("DOWNLOAD_DELAY", 0.5)

    runner = CrawlerRunner(settings)
    archive_urls = reversed([f"https://semianalysis.com/archives/page/{n}/" for n in range(1, 24)])

    @defer.inlineCallbacks
    def crawl():
        for archive_url in archive_urls:
            yield runner.crawl(
                ArticleCrawler,
                archive_url=archive_url,
                output_path=DEFAULT_PATH,
            )
        reactor.stop()

    crawl()
    reactor.run()  # Blocks until reactor.stop() is called.


if __name__ == "__main__":
    main()

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import scrapy

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
        self.articles: list[dict[str, str]] = []

    def parse(self, response: scrapy.http.Response) -> Iterator[scrapy.Request]:
        """Parse the archive page and follow links to individual articles."""
        # Find all article links - adjust selector based on actual HTML structure
        article_links = response.css("a::attr(href)").getall()
        for link in article_links:
            absolute_url = response.urljoin(link)
            if absolute_url.startswith("https://semianalysis.com/20"):
                yield scrapy.Request(absolute_url, callback=self.parse_article)

    def parse_article(self, response: scrapy.http.Response) -> None:
        """Parse and save individual article content."""
        title = response.css("title::text").get() or "untitled"
        text_fragments = response.css("div.entry-content *::text").getall()
        content = " ".join(text_fragments).strip()

        self.save(
            {
                "url": response.url,
                "list_url": self.start_urls[0],
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "content": content,
            }
        )

    def save(self, article) -> None:
        """Save all collected articles to the output file."""

        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(article, ensure_ascii=False, sort_keys=False) + "\n")

        self.articles = []


# To run sequential crawls without restarting the reactor:
def main():
    from scrapy.crawler import CrawlerRunner
    from scrapy.utils.log import configure_logging
    from scrapy.utils.project import get_project_settings
    from twisted.internet import defer, reactor

    configure_logging()
    settings = get_project_settings()
    # Set low concurrency and add a download delay
    settings.set("CONCURRENT_REQUESTS", 1)
    settings.set("DOWNLOAD_DELAY", 0.5)

    runner = CrawlerRunner(settings)
    archive_urls = [f"https://semianalysis.com/archives/page/{n}/" for n in range(1, 24)]

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

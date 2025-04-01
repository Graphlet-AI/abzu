import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import scrapy


# https://semianalysis.com/archives/page/1/
class ArticleCrawler(scrapy.Spider):
    name = "article_crawler"

    def __init__(
        self, archive_url: str, output_path: str = "data/articles.json", *args: Any, **kwargs: Any
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
                time.sleep(0.5)
                yield scrapy.Request(absolute_url, callback=self.parse_article)

    def parse_article(self, response: scrapy.http.Response) -> None:
        """Parse and save individual article content."""
        # Extract title for filename - adjust selector based on actual HTML
        title = response.css("title::text").get() or "untitled"

        # Extract article text content from entry-content div
        # content = " ".join(response.css("div.entry-content::text").getall()).strip()

        # Extract all text within the div with class 'entry-content'
        text_fragments = response.css("div.entry-content *::text").getall()

        # Join the fragments and remove extra whitespace
        content = " ".join(text_fragments).strip()

        # Save article
        self.articles.append(
            {
                "url": response.url,
                "title": title,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.save()

    def save(self) -> None:
        """Save all collected articles to the output file."""
        import json

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)


# To run:
# scrapy runspider crawl.py -a archive_url="https://semianalysis.com/archives/"


def main():
    """Run the crawler from Python."""
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = CrawlerProcess(get_project_settings())
    process.crawl(
        ArticleCrawler, archive_url="https://semianalysis.com/archives/", output_dir="articles"
    )
    process.start()


if __name__ == "__main__":
    main()

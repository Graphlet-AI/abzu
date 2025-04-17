#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import IndustryArticle
from abzu.utils import load_jsonl, save_jsonl

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_articles(file_path: str) -> List[Dict[str, Any]]:
    """Load articles from a JSONL file."""
    logger.info(f"Loading articles from {file_path}")
    articles = load_jsonl(file_path)
    logger.info(f"Loaded {len(articles)} articles")
    return articles


async def process_article_async(article: Dict[str, Any]) -> Optional[IndustryArticle]:
    """Process an article using BAML asynchronously."""
    article_text = article.get("content", "")

    if not article_text:
        logger.warning(f"Empty article text for article: {article.get('id', 'unknown')}")
        return None

    try:
        result = await async_b.ExtractIndustryArticle(article_text)

        # Pass through timestamps from the original article
        result.collected_at = article.get("collected_at", None)
        result.published_at = article.get("published_at", None)

        logger.info(f"Processed article: {article.get('title', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to process article: {article.get('title', 'unknown')} - {e}")
        return None


async def process_batch(
    batch: List[Dict[str, Any]],
) -> List[Optional[IndustryArticle | BaseException]]:
    """Process a batch of articles concurrently."""
    logger.info(f"Processing batch of {len(batch)} articles")
    start_time = time.time()

    # Create task for each article in the batch
    tasks = [process_article_async(article) for article in batch]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed_results: list[Optional[IndustryArticle | BaseException]] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error processing article: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)

    elapsed_time = time.time() - start_time
    logger.info(f"Batch processed in {elapsed_time:.2f} seconds")

    return processed_results


def save_results(results: List[Optional[IndustryArticle]], output_path: str) -> None:
    """Save processed results to a JSONL file."""
    valid_results = [r.model_dump() for r in results if r is not None]

    if save_jsonl(valid_results, output_path, create_backup=True):
        logger.info(f"Saved {len(valid_results)} processed articles to {output_path}")
        if Path(f"{output_path}.bak").exists():
            logger.info(f"Backup created: {output_path}.bak")
    else:
        logger.error(f"Failed to save results to {output_path}")


async def process_articles_async(
    articles: List[Dict[str, Any]], output_file: str, batch_size: int
) -> None:
    """Process all articles in batches asynchronously."""
    # Process in batches
    all_results: list[Optional[IndustryArticle | BaseException]] = []
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1}/{(len(articles) + batch_size - 1) // batch_size}"
        )
        batch_results = await process_batch(batch)
        all_results.extend(batch_results)

    # Save all results
    save_results(all_results, output_file)  # type: ignore


async def async_main(
    input_file: str = "data/articles.jsonl",
    output_file: str = "data/processed_articles.jsonl",
    batch_size: int = 5,
) -> int:
    """Async main function."""
    # Check for required environment variables
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is not set")
        logger.error("Please set it with: export GEMINI_API_KEY=your_api_key")
        return 1

    # Load articles
    articles = load_articles(input_file)
    if not articles:
        logger.error("No articles to process")
        return 1

    # Process articles in batches asynchronously
    start_time = time.time()
    await process_articles_async(articles, output_file, batch_size)
    total_time = time.time() - start_time

    logger.info(f"Processing complete. Total time: {total_time:.2f} seconds")
    return 0


def process_main(
    input_file: str = "data/articles.jsonl",
    output_file: str = "data/processed_articles.jsonl",
    batch_size: int = 5,
) -> int:
    """Process articles main function."""
    return asyncio.run(async_main(input_file, output_file, batch_size))


def main() -> int:
    """Command line interface for process_articles."""
    return process_main()


if __name__ == "__main__":
    sys.exit(main())

"""Article processing module for Abzu."""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import IndustryArticle
from abzu.config import config
from abzu.utils import load_jsonl, save_jsonl

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_articles(file_path: str) -> list[dict[str, Any]]:
    """Load articles from a JSONL file and deduplicate them.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        List of deduplicated article dictionaries
    """
    logger.info(f"Loading articles from {file_path}")
    articles = load_jsonl(file_path)
    logger.info(f"Loaded {len(articles)} articles")

    # Deduplicate articles by URL
    from abzu.utils import deduplicate_articles

    deduped_articles = deduplicate_articles(articles)
    logger.info(f"After deduplication: {len(deduped_articles)} unique articles")

    return deduped_articles


async def process_article_async(
    article: dict[str, Any],
) -> IndustryArticle | BaseException | None:
    """Process an article using BAML asynchronously.

    Args:
        article: Dictionary containing article data

    Returns:
        Processed IndustryArticle object or None if processing failed
    """
    article_text = article.get("content", "")

    if not article_text:
        logger.warning(f"Empty article content for article: {article.get('id', 'unknown')}")
        return None

    try:
        # Content is already extracted text, just pass it to BAML
        logger.info(
            f"Processing article: {article.get('title', 'unknown')} ({len(article_text):,} chars)"
        )

        result = await async_b.ExtractIndustryArticle(article_text)

        # Pass through timestamps from the original article
        result.collected_at = article.get("collected_at", None)
        result.posted_at = article.get("posted_at", None)

        # Pass through the article URL
        result.url = article.get("url", None)

        logger.info(f"Processed article: {article.get('title', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Failed to process article: {article.get('title', 'unknown')} - {e}")
        return None


async def process_batch(
    batch: list[dict[str, Any]],
) -> list[IndustryArticle | BaseException | None]:
    """Process a batch of articles concurrently.

    Args:
        batch: List of article dictionaries to process

    Returns:
        List of processed articles or exceptions
    """
    logger.info(f"Processing batch of {len(batch)} articles")
    start_time = time.time()

    # Create task for each article in the batch
    tasks = [process_article_async(article) for article in batch]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed_results: list[IndustryArticle | BaseException | None] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error processing article: {result}")
            processed_results.append(None)
        else:
            processed_results.append(result)

    elapsed_time = time.time() - start_time
    logger.info(f"Batch processed in {elapsed_time:.2f} seconds")

    return processed_results


def save_results(results: list[IndustryArticle | BaseException | None], output_path: str) -> None:
    """Save processed results to a JSONL file.

    Args:
        results: List of processed IndustryArticle objects
        output_path: Path to write the results
    """
    valid_results = [r.model_dump() for r in results if r is not None]  # type: ignore

    if save_jsonl(valid_results, output_path, create_backup=True):
        logger.info(f"Saved {len(valid_results)} processed articles to {output_path}")
        if Path(f"{output_path}.bak").exists():
            logger.info(f"Backup created: {output_path}.bak")
    else:
        logger.error(f"Failed to save results to {output_path}")


async def process_articles_async(
    articles: list[dict[str, Any]], output_file: str, batch_size: int
) -> None:
    """Process all articles in batches asynchronously.

    Args:
        articles: List of article dictionaries
        output_file: Path to write results
        batch_size: Number of articles to process in each batch
    """
    # Process in batches
    all_results: list[IndustryArticle | BaseException | None] = []
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1}/{(len(articles) + batch_size - 1) // batch_size}"
        )
        batch_results = await process_batch(batch)
        all_results.extend(batch_results)

    # Save all results
    save_results(all_results, output_file)


async def async_main(
    input_file: str = config.get("process.articles.semianalysis.input"),
    output_file: str = config.get("process.articles.semianalysis.output"),
    batch_size: int = 5,
) -> int:
    """Async main function for article processing.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file
        batch_size: Number of articles to process in each batch

    Returns:
        0 on success, 1 on failure
    """
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
    input_file: str = config.get("process.articles.semianalysis.input"),
    output_file: str = config.get("process.articles.semianalysis.output"),
    batch_size: int = 5,
) -> int:
    """Process articles main function.

    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file
        batch_size: Number of articles to process in each batch

    Returns:
        0 on success, 1 on failure
    """
    return asyncio.run(async_main(input_file, output_file, batch_size))

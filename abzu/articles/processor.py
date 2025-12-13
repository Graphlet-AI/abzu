"""Article processing module for Abzu."""

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from baml_py import ClientRegistry
from baml_py.internal_monkeypatch import BamlValidationError
from tqdm import tqdm

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import IndustryArticle
from abzu.config import config
from abzu.logs import get_logger
from abzu.utils import load_jsonl, save_jsonl

logger = get_logger(__name__)


# Titles that indicate blocked or invalid articles (Cloudflare, CAPTCHA, etc.)
INVALID_TITLES = [
    "just a moment...",
    "access denied",
    "please wait...",
    "checking your browser",
    "attention required",
    "one more step",
    "verify you are human",
]

# Minimum content length for a valid article (in characters)
MIN_CONTENT_LENGTH = 200


def is_valid_article(article: dict[str, Any]) -> bool:
    """Check if an article is valid for processing.

    Filters out Cloudflare-blocked pages, CAPTCHAs, and articles with insufficient content.

    Args:
        article: Dictionary containing article data

    Returns:
        True if article is valid for processing, False otherwise
    """
    title = (article.get("title") or "").lower().strip()
    content = article.get("content") or ""

    # Check for blocked/invalid titles
    for invalid_title in INVALID_TITLES:
        if invalid_title in title:
            return False

    # Check minimum content length
    if len(content) < MIN_CONTENT_LENGTH:
        return False

    return True


def load_articles(file_path: str) -> list[dict[str, Any]]:
    """Load articles from a JSONL file, deduplicate and filter invalid ones.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        List of valid, deduplicated article dictionaries
    """
    logger.info(f"Loading articles from {file_path}")
    articles = load_jsonl(file_path)
    logger.info(f"Loaded {len(articles)} articles")

    # Deduplicate articles by URL
    from abzu.utils import deduplicate_articles

    deduped_articles = deduplicate_articles(articles)
    logger.info(f"After deduplication: {len(deduped_articles)} unique articles")

    # Filter out invalid articles (Cloudflare blocks, CAPTCHAs, too short)
    valid_articles = [a for a in deduped_articles if is_valid_article(a)]
    filtered_count = len(deduped_articles) - len(valid_articles)
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} invalid articles (blocked/too short)")
    logger.info(f"Valid articles for processing: {len(valid_articles)}")

    return valid_articles


def get_client_registry() -> ClientRegistry:

    cr: ClientRegistry = ClientRegistry()

    cr.add_llm_client(
        name="Gemini25Flash",
        provider="google-ai",
        options={
            "model": "gemini-2.5-flash",
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "generationConfig": {
                "temperature": 0.0,
            },
        },
    )

    cr.add_llm_client(
        name="Gemini25Pro",
        provider="google-ai",
        options={
            "model": "gemini-2.5-pro",
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "generationConfig": {
                "temperature": 0.0,
            },
        },
    )

    # Start with cheaper Gemini 2.5 Flash, fall back to 2.5 Pro
    cr.set_primary("Gemini25Flash")

    return cr


async def process_article_async(
    article: dict[str, Any],
) -> IndustryArticle | BaseException | None:
    """Process an article using BAML asynchronously.

    Args:
        article: Dictionary containing article data

    Returns:
        Processed IndustryArticle object or None if processing failed
    """
    # cr: ClientRegistry = get_client_registry()

    article_text = article.get("content", "")

    if not article_text:
        logger.warning(f"Empty article content for article: {article.get('id', 'unknown')}")
        return None

    try:
        # Content is already extracted text, just pass it to BAML
        logger.info(
            f"Processing article: {article.get('title') or 'Empty Article'} posted at {article.get('posted_at') or 'Unknown Time'} ({len(article_text):,} chars)"
        )

        #
        # Will try this later...
        #

        # try:
        #     result = await async_b.ExtractIndustryArticle(article_text, {"client_registry": cr})
        # except BamlValidationError as e:
        #     logger.error(f"BAML validation error: {e}")
        #     # Retry exceptions with Gemini 2.5 Pro
        #     cr.set_primary("Gemini25Pro")
        #     result = await async_b.ExtractIndustryArticle(article_text, {"client_registry": cr})
        # finally:
        #     cr.set_primary("Gemini25Flash")

        try:
            result = await async_b.ExtractIndustryArticle(article_text)
        except BamlValidationError as e:
            logger.error(f"BAML validation error: {e}")
            return None

        # Pass through timestamps from the original article
        result.collected_at = article.get("collected_at", None)
        result.posted_at = article.get("posted_at", None)

        # Pass through the article URL
        result.url = article.get("url", None)

        # Pass through any title
        result.title = article.get("title", result.title)

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
    # Process in batches - starting with the most recent articles
    all_results: list[IndustryArticle | BaseException | None] = []
    batch_indices = list(reversed(range(0, len(articles), batch_size)))
    total_batches = len(batch_indices)

    for batch_num, i in enumerate(
        tqdm(batch_indices, desc="Processing articles", unit="batch"), start=1
    ):
        batch = articles[i : i + batch_size]
        logger.info(f"Processing batch {batch_num}/{total_batches}")
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

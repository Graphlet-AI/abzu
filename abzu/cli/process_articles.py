#!/usr/bin/env python3
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from abzu.baml_client import b
from abzu.baml_client.types import IndustryArticle

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_articles(file_path: str) -> List[Dict[str, Any]]:
    """Load articles from a JSONL file."""
    articles = []
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    logger.info(f"Loading articles from {file_path}")
    with open(path, "r") as f:
        for line in f:
            try:
                article = json.loads(line.strip())
                articles.append(article)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse line: {line}")
                continue

    logger.info(f"Loaded {len(articles)} articles")
    return articles


def process_article(article: Dict[str, Any]) -> IndustryArticle:
    """Process an article using BAML."""
    article_text = article.get("content", "")

    if not article_text:
        logger.warning(f"Empty article text for article: {article.get('id', 'unknown')}")
        return IndustryArticle(title="", summary="")

    logger.info(f"Processing article: {article.get('title', 'unknown')}")
    try:
        result = b.ExtractIndustryArticle(article_text)

        # Pass through timestamps from the original article
        result.collected_at = article.get("published_at", None)
        result.published_at = article.get("published_at", None)
        return result
    except Exception as e:
        logger.error(f"Failed to process article: {e}")
        return IndustryArticle(title="", summary="")


def save_results(results: List[IndustryArticle], output_path: str) -> None:
    """Save processed results to a JSONL file."""
    with open(output_path, "w") as f:
        for result in results:
            if result:
                f.write(json.dumps(result.model_dump()) + "\n")

    logger.info(f"Saved {len([r for r in results if r])} processed articles to {output_path}")


def process_main(
    input_file: str = "data/articles.jsonl", output_file: str = "data/processed_articles.jsonl"
) -> int:
    """Process articles main function."""
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

    # Process articles
    results = []
    for article in articles:
        result = process_article(article)
        results.append(result)

    # Save results
    save_results(results, output_file)
    logger.info("Processing complete")
    return 0


def main() -> int:
    """Command line interface for process_articles."""
    return process_main()


if __name__ == "__main__":
    sys.exit(main())

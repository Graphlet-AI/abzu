"""Process URLs into IndustryArticle objects using BAML."""

import logging
import os
from typing import Any, Union

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import IndustryArticle
from abzu.html_extractor import HTMLExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArticleProcessor:
    """Process articles using BAML's IndustryArticle extraction."""

    def __init__(self):
        """Initialize the article processor."""
        # Check for required environment variables
        if not os.environ.get("GEMINI_API_KEY"):
            logger.warning(
                "GEMINI_API_KEY environment variable is not set. "
                "BAML article processing may fail."
            )

        # Initialize HTML extractor
        self.html_extractor = HTMLExtractor()

    async def process_article(
        self, article: dict[str, Any]
    ) -> tuple[bool, Union[IndustryArticle, str]]:
        """Process an article using BAML.

        Args:
            article: Dictionary containing article data with 'content' field

        Returns:
            Tuple containing:
                - Success status (True/False)
                - Either the processed IndustryArticle (on success) or an error message (on failure)
        """
        html_content = article.get("content", "")

        if not html_content:
            error_msg = f"Empty article content for URL: {article.get('url', 'unknown')}"
            logger.warning(error_msg)
            return False, error_msg

        try:
            # Extract text from HTML to reduce token count
            article_text = self.html_extractor.extract(html_content)

            # Log the reduction in size
            original_size = len(html_content)
            extracted_size = len(article_text)
            reduction_pct = (
                ((original_size - extracted_size) / original_size * 100) if original_size > 0 else 0
            )
            logger.info(
                f"Extracted text from HTML for {article.get('title', 'unknown')}: "
                f"{original_size:,} → {extracted_size:,} chars ({reduction_pct:.1f}% reduction)"
            )

            # Process the article using BAML
            logger.info(f"Processing article: {article.get('title', 'unknown')}")
            result = await async_b.ExtractIndustryArticle(article_text)

            # Pass through timestamps from the original article
            result.collected_at = article.get("collected_at")
            result.posted_at = article.get("posted_at")

            # Pass through the article URL
            result.url = article.get("url")

            logger.info(f"Successfully processed article: {article.get('title', 'unknown')}")
            return True, result
        except Exception as e:
            error_msg = f"Failed to process article: {article.get('title', 'unknown')} - {e}"
            logger.error(error_msg)
            return False, error_msg

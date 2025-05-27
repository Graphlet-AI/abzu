"""I/O utilities for Chat agent."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from abzu.baml_client.types import IndustryArticle

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArticleStorage:
    """Storage class for raw articles and processed IndustryArticle documents."""

    def __init__(
        self,
        raw_articles_path: str = "data/chat/raw_articles.jsonl",
        processed_articles_path: str = "data/chat/processed_articles.jsonl",
        create_dirs: bool = True,
    ):
        """Initialize the storage.

        Args:
            raw_articles_path: Path to store raw article data. Defaults to "data/chat/raw_articles.jsonl".
            processed_articles_path: Path to store processed article data. Defaults to "data/chat/processed_articles.jsonl".
            create_dirs: Whether to create directories if they don't exist. Defaults to True.
        """
        self.raw_articles_path = raw_articles_path
        self.processed_articles_path = processed_articles_path

        if create_dirs:
            self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure that the storage directories exist."""
        for path in [self.raw_articles_path, self.processed_articles_path]:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def save_raw_article(self, article: dict[str, Any]) -> bool:
        """Save a raw article to the storage.

        Args:
            article: Article data dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Generate a backup if file exists and it's time for backup
            self._create_backup_if_needed(self.raw_articles_path)

            # Append the article to the file
            with open(self.raw_articles_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(article) + "\n")

            logger.info(f"Saved raw article to {self.raw_articles_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save raw article: {e}")
            return False

    def save_processed_article(self, article: IndustryArticle) -> bool:
        """Save a processed IndustryArticle to the storage.

        Args:
            article: Processed IndustryArticle object

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Generate a backup if file exists and it's time for backup
            self._create_backup_if_needed(self.processed_articles_path)

            # Append the article to the file
            with open(self.processed_articles_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(article.model_dump()) + "\n")

            logger.info(f"Saved processed article to {self.processed_articles_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save processed article: {e}")
            return False

    def _create_backup_if_needed(self, file_path: str) -> None:
        """Create a backup of the file if it exists and it's time to do so.

        Creates a backup with the current date if the file exists
        and has not been backed up today.

        Args:
            file_path: Path to the file to backup
        """
        p = Path(file_path)
        if not p.exists():
            return

        # Check if we should create a backup
        today = datetime.now().strftime("%Y-%m-%d")
        backup_path = f"{file_path}.{today}.bak"

        # Only backup once per day
        if not Path(backup_path).exists():
            try:
                os.makedirs(os.path.dirname(os.path.abspath(backup_path)), exist_ok=True)
                with open(file_path, "r", encoding="utf-8") as src_file:
                    with open(backup_path, "w", encoding="utf-8") as bak_file:
                        bak_file.write(src_file.read())
                logger.info(f"Created backup of {file_path} at {backup_path}")
            except Exception as e:
                logger.error(f"Failed to create backup of {file_path}: {e}")

    def load_raw_articles(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Load raw articles from storage.

        Args:
            limit: Maximum number of articles to load. Defaults to None (all).

        Returns:
            List of article dictionaries
        """
        return self._load_jsonl(self.raw_articles_path, limit)

    def load_processed_articles(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Load processed articles from storage.

        Args:
            limit: Maximum number of articles to load. Defaults to None (all).

        Returns:
            List of processed article dictionaries
        """
        return self._load_jsonl(self.processed_articles_path, limit)

    def _load_jsonl(self, file_path: str, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Load JSON Lines file.

        Args:
            file_path: Path to the file
            limit: Maximum number of lines to load. Defaults to None (all).

        Returns:
            List of dictionaries
        """
        items = []
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if limit is not None and i >= limit:
                        break
                    line = line.strip()
                    if line:  # Skip empty lines
                        items.append(json.loads(line))

            logger.info(f"Loaded {len(items)} items from {file_path}")
            return items
        except Exception as e:
            logger.error(f"Failed to load from {file_path}: {e}")
            return []

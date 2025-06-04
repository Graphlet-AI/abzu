"""Utility functions for Abzu."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Union

from abzu.logs import get_logger

logger = get_logger(__name__)


def backup_file(file_path: Union[str, Path]) -> bool:
    """
    Create a backup of a file if it exists.

    Args:
        file_path: Path to the file to backup

    Returns:
        bool: True if backup was created, False otherwise
    """
    path = Path(file_path)
    if not path.exists():
        return False

    backup_path = Path(f"{path}.bak")
    try:
        shutil.copy2(path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {path}: {e}")
        return False


def save_jsonl(
    data: list[dict[str, Any]], file_path: Union[str, Path], create_backup: bool = True
) -> bool:
    """
    Save data to a JSONL file with backup option.

    Args:
        data: List of dictionaries to save
        file_path: Path to save the file
        create_backup: Whether to create a backup of the file if it exists

    Returns:
        bool: True if successful, False otherwise
    """
    path = Path(file_path)

    # Create directory if it doesn't exist
    os.makedirs(path.parent, exist_ok=True)

    # Create backup if requested and file exists
    if create_backup:
        backup_file(path)

    try:
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {path}: {e}")
        return False


def append_jsonl(
    data: dict[str, Any], file_path: Union[str, Path], create_backup: bool = True
) -> bool:
    """
    Append a record to a JSONL file with backup option.
    Prevents duplicate URLs from being added.

    Args:
        data: Dictionary to append
        file_path: Path to the file
        create_backup: Whether to create a backup of the file if it exists

    Returns:
        bool: True if successful, False otherwise
    """
    path = Path(file_path)

    # Create directory if it doesn't exist
    os.makedirs(path.parent, exist_ok=True)

    # Check if this URL already exists in the file
    if path.exists() and "url" in data:
        # Use a set for faster lookup
        existing_urls = set()
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        item = json.loads(line.strip())
                        if "url" in item:
                            existing_urls.add(item["url"])
                    except (json.JSONDecodeError, Exception):
                        # Skip invalid lines
                        pass

            # If URL already exists, don't append
            if data["url"] in existing_urls:
                logger.info(f"Skipping duplicate URL: {data['url']}")
                return True
        except Exception as e:
            logger.error(f"Error checking for duplicates in {path}: {e}")
            # Continue with append operation if we can't check for duplicates

    # Create backup if requested and file exists
    if create_backup and path.exists():
        backup_file(path)

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to append data to {path}: {e}")
        return False


def load_jsonl(file_path: Union[str, Path]) -> list[dict[str, Any]]:
    """
    Load data from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of dictionaries loaded from the file
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {path}")
        return []

    data = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    data.append(item)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse line: {line}")
    except Exception as e:
        logger.error(f"Failed to load data from {path}: {e}")

    return data


def build_crawled_url_index(file_path: Union[str, Path]) -> set[str]:
    """
    Read a JSONL file and build an index of already crawled URLs.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        Set of URLs that have already been crawled
    """
    path = Path(file_path)
    crawled_urls: set[str] = set()

    if not path.exists():
        logger.info(f"No existing articles file found at {path}, starting fresh")
        return crawled_urls

    try:
        # Count entries for logging
        total_entries = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if "url" in item:
                        crawled_urls.add(item["url"])
                    total_entries += 1
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line in {path}")
                except Exception as e:
                    logger.warning(f"Error processing line in {path}: {e}")
        logger.info(
            f"Loaded {len(crawled_urls)} unique URLs from {total_entries} entries in {path}"
        )
    except Exception as e:
        logger.error(f"Failed to build URL index from {path}: {e}")

    return crawled_urls


def deduplicate_articles(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deduplicate articles based on URL.

    Args:
        data: List of articles to deduplicate

    Returns:
        Deduplicated list of articles
    """
    if not data:
        return []

    # Use a dictionary to keep only the latest version of each article by URL
    unique_articles: dict[str, dict[str, Any]] = {}

    for article in data:
        if "url" in article:
            url = article["url"]
            # Keep this article if we haven't seen this URL before
            # Or if we have an existing article but this one is newer (based on collected_at)
            if url not in unique_articles or (
                "collected_at" in article
                and "collected_at" in unique_articles[url]
                and article["collected_at"] > unique_articles[url]["collected_at"]
            ):
                unique_articles[url] = article
        else:
            # Keep articles without URLs (though they should always have URLs)
            logger.warning("Found article without URL, keeping it anyway")
            # Use a random key for articles without URLs
            unique_articles[f"no_url_{len(unique_articles)}"] = article

    deduped_data = list(unique_articles.values())
    logger.info(f"Deduplicated {len(data)} articles to {len(deduped_data)} unique articles")
    return deduped_data

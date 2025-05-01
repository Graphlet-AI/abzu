"""Utility functions for Abzu."""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set, Union

logger = logging.getLogger(__name__)


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
    data: List[Dict[str, Any]], file_path: Union[str, Path], create_backup: bool = True
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
    data: Dict[str, Any], file_path: Union[str, Path], create_backup: bool = True
) -> bool:
    """
    Append a record to a JSONL file with backup option.

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


def load_jsonl(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
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


def build_crawled_url_index(file_path: Union[str, Path]) -> Set[str]:
    """
    Read a JSONL file and build an index of already crawled URLs.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        Set of URLs that have already been crawled
    """
    path = Path(file_path)
    crawled_urls: Set[str] = set()

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

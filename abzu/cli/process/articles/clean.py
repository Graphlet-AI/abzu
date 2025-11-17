"""Clean processed article files by backing them up and removing them."""

import shutil
from datetime import datetime
from pathlib import Path

import click

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command()
def clean() -> None:
    """Back up and remove all processed_* files from data/articles/."""
    articles_dir = Path(config.get("data.articles_dir", "data/articles"))

    # Ensure articles directory exists
    if not articles_dir.exists():
        click.echo(f"Articles directory {articles_dir} does not exist.")
        return

    # Find all processed_* files
    processed_files = list(articles_dir.glob("processed_*"))

    if not processed_files:
        click.echo("No processed files found to clean.")
        return

    # Create timestamped backup directory in /tmp/articles/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path("/tmp/articles") / f"abzu_articles_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Found {len(processed_files)} processed files to clean:")

    # Back up each file
    for file_path in processed_files:
        try:
            backup_path = backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            click.echo(f"  Backed up: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {e}")
            click.echo(f"  ERROR backing up {file_path.name}: {e}")
            return

    # Remove original files
    click.echo("\nRemoving original processed files:")
    for file_path in processed_files:
        try:
            file_path.unlink()
            click.echo(f"  Removed: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to remove {file_path}: {e}")
            click.echo(f"  ERROR removing {file_path.name}: {e}")
            return

    click.echo(f"\nBackup location: {backup_dir}")
    click.echo(
        "All processed files have been cleaned. Fresh data will be generated on next process run."
    )

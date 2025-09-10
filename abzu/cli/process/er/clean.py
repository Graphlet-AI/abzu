"""CLI for cleaning entity resolution output files."""

import shutil
from pathlib import Path

import click

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "--base-path",
    default=config.get("process.kg.er.paths.base", "data/er"),
    help="Base path for entity resolution data",
)
@click.option(
    "--iteration",
    "-i",
    type=int,
    help="Clean only specific iteration (if not set, cleans all)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean(base_path: str, iteration: int | None, dry_run: bool, force: bool) -> None:
    """Clean entity resolution output files to ensure clean state between runs."""
    base = Path(base_path)

    # Define patterns to clean
    patterns_to_clean = [
        "*_blocks.parquet",
        "*_blocks.json",
        "all_blocks.parquet",
        "all_blocks.json",
        "combined_blocks.parquet",
        "combined_blocks.json",
        "matches.parquet",
        "matches.json",
        "matches.jsonl",
        "matches.jsonl.bak",
        "matches_backup_*.parquet",
        "matches_backup_*.json",
        "matches_backup_*.jsonl",
        "companies_resolved.parquet",
        "companies_resolved.json",
        "er_evaluation_metrics.parquet",
        "er_evaluation_metrics.json",
    ]

    files_to_delete: list[Path] = []

    if iteration is not None:
        # Clean specific iteration
        iter_path = base / "iterations" / str(iteration)
        if iter_path.exists():
            for pattern in patterns_to_clean:
                files_to_delete.extend(iter_path.glob(pattern))
        else:
            click.echo(f"Iteration directory {iter_path} does not exist")
            return
    else:
        # Clean base directory files
        for pattern in patterns_to_clean:
            files_to_delete.extend(base.glob(pattern))

        # Clean all iteration directories
        iterations_path = base / "iterations"
        if iterations_path.exists():
            for iter_dir in iterations_path.iterdir():
                if iter_dir.is_dir() and iter_dir.name.isdigit():
                    for pattern in patterns_to_clean:
                        files_to_delete.extend(iter_dir.glob(pattern))

    if not files_to_delete:
        click.echo("No files found to clean")
        return

    # Display files to be deleted
    click.echo(f"Found {len(files_to_delete)} files/directories to clean:")
    for file in sorted(files_to_delete):
        relative_path = (
            file.relative_to(base.parent.parent) if base.parent.parent in file.parents else file
        )
        click.echo(f"  - {relative_path}")

    if dry_run:
        click.echo("\nDry run mode - no files were deleted")
        return

    # Confirm deletion
    if not force:
        if not click.confirm("\nDo you want to delete these files?"):
            click.echo("Cleanup cancelled")
            return

    # Delete files
    deleted_count = 0
    error_count = 0
    for file in files_to_delete:
        try:
            if file.is_dir():
                shutil.rmtree(file)
                logger.debug(f"Deleted directory: {file}")
            else:
                file.unlink()
                logger.debug(f"Deleted file: {file}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete {file}: {e}")
            error_count += 1

    click.echo(f"\nDeleted {deleted_count} files/directories")
    if error_count > 0:
        click.echo(f"Failed to delete {error_count} files/directories")

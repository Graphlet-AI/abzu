import tarfile
from pathlib import Path
from typing import Optional

from abzu.data.utils import (
    collect_output_paths,
    find_existing_files_and_backups,
    get_relative_path_from_root,
)
from abzu.logs import get_logger

logger = get_logger(__name__)


def export_data(
    output_file: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> str:
    """
    Export all data files defined by output keys in config.yml to a tarball.

    Args:
        output_file: Output tarball path. If None, generates timestamped filename
        dry_run: If True, show what would be exported without creating tarball
        verbose: Enable verbose logging

    Returns:
        Path to created tarball (empty string if dry_run)
    """
    logger.info("Starting data export...")

    # Get project root directory
    project_root = Path.cwd()

    # Collect all output paths from config
    logger.info("Collecting output paths from config...")
    output_paths = collect_output_paths()

    if not output_paths:
        logger.warning("No output paths found in config")
        return ""

    logger.info(f"Found {len(output_paths)} output paths in config")

    # Find existing files and their backups
    logger.info("Checking for existing files and backups...")
    existing_files = find_existing_files_and_backups(output_paths)

    if not existing_files:
        logger.warning("No existing files found to export")
        return ""

    # Generate output filename if not provided
    if not output_file:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"abzu_data_export_{timestamp}.tar.gz"

    # Make sure output file is in project root
    output_path = project_root / output_file

    logger.info(
        f"Will export {sum(len(files) for files in existing_files.values())} files/directories"
    )

    if verbose or dry_run:
        logger.info("Files to be exported:")
        for original_path, files in existing_files.items():
            logger.info(f"  {original_path}:")
            for file_path in files:
                rel_path = get_relative_path_from_root(file_path, str(project_root))
                logger.info(f"    -> {rel_path}")

    if dry_run:
        logger.info(f"Dry run complete. Would create: {output_path}")
        return ""

    # Create the tarball
    logger.info(f"Creating tarball: {output_path}")

    try:
        with tarfile.open(output_path, "w:gz") as tar:
            for original_path, files in existing_files.items():
                for file_path in files:
                    file_path_obj = Path(file_path)

                    if not file_path_obj.exists():
                        logger.warning(f"File no longer exists, skipping: {file_path}")
                        continue

                    # Get the relative path from project root
                    rel_path = get_relative_path_from_root(file_path, str(project_root))

                    logger.debug(f"Adding to tarball: {file_path} -> {rel_path}")

                    try:
                        # Exclude hidden files from directories to avoid duplicates and checksum files
                        if file_path_obj.is_dir():

                            def exclude_hidden_files(
                                tarinfo: tarfile.TarInfo,
                            ) -> Optional[tarfile.TarInfo]:
                                if tarinfo.name.split("/")[-1].startswith("."):
                                    return None
                                return tarinfo

                            tar.add(file_path, arcname=rel_path, filter=exclude_hidden_files)
                        else:
                            tar.add(file_path, arcname=rel_path)
                        if verbose:
                            logger.info(f"  Added: {rel_path}")
                    except Exception as e:
                        logger.error(f"Failed to add {file_path}: {e}")

        logger.info(f"Export completed successfully: {output_path}")
        logger.info(f"Tarball size: {output_path.stat().st_size / (1024 * 1024):.1f} MB")

        return str(output_path)

    except Exception as e:
        logger.error(f"Failed to create tarball: {e}")
        # Clean up partial file
        if output_path.exists():
            output_path.unlink()
        raise


def list_exportable_data() -> None:
    """
    List all data that would be exported without creating a tarball.
    """
    logger.info("Listing exportable data...")

    output_paths = collect_output_paths()
    existing_files = find_existing_files_and_backups(output_paths)

    if not existing_files:
        logger.info("No exportable data found")
        return

    total_size = 0
    total_files = 0

    logger.info("Exportable data:")
    for original_path, files in existing_files.items():
        logger.info(f"  {original_path}:")
        for file_path in files:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                if file_path_obj.is_file():
                    size = file_path_obj.stat().st_size
                    total_size += size
                    total_files += 1
                    logger.info(f"    {file_path} ({size / (1024 * 1024):.1f} MB)")
                else:
                    # Directory - estimate size
                    dir_size = sum(
                        f.stat().st_size for f in file_path_obj.rglob("*") if f.is_file()
                    )
                    dir_files = len(list(file_path_obj.rglob("*")))
                    total_size += dir_size
                    total_files += dir_files
                    logger.info(
                        f"    {file_path}/ ({dir_size / (1024 * 1024):.1f} MB, {dir_files} files)"
                    )

    logger.info(f"Total: {total_files} files, {total_size / (1024 * 1024):.1f} MB")

import tarfile
from pathlib import Path
from typing import Optional

from abzu.data.export import export_data
from abzu.data.utils import create_backup_filename
from abzu.logs import get_logger

logger = get_logger(__name__)


def import_data(
    input_file: str,
    create_backup: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = True,
) -> Optional[str]:
    """
    Import data from a tarball, optionally creating a backup first.

    Args:
        input_file: Path to input tarball
        create_backup: Whether to create a backup before importing
        overwrite: Whether to overwrite existing files without prompting
        dry_run: If True, show what would be imported without making changes
        verbose: Enable verbose logging

    Returns:
        Path to backup file if created, None otherwise
    """
    logger.info(f"Starting data import from: {input_file}")

    # Validate input file
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if not tarfile.is_tarfile(input_file):
        raise ValueError(f"File is not a valid tarball: {input_file}")

    # Get project root directory
    project_root = Path.cwd()
    backup_path: Optional[str] = None

    # Create backup if requested
    if create_backup and not dry_run:
        logger.info("Creating backup of existing data...")
        backup_filename = create_backup_filename()
        backup_path = export_data(
            output_file=backup_filename,
            dry_run=False,
            verbose=verbose,
        )
        if backup_path:
            logger.info(f"Backup created: {backup_path}")
        else:
            logger.info("No existing data to backup")

    # Examine tarball contents
    logger.info("Examining tarball contents...")

    try:
        with tarfile.open(input_file, "r:*") as tar:
            members = tar.getmembers()

            if not members:
                logger.warning("Tarball is empty")
                return backup_path

            logger.info(f"Tarball contains {len(members)} items")

            # Validate that all paths are within expected directories
            for member in members:
                # Ensure paths are safe (no .. traversal)
                if ".." in member.name or member.name.startswith("/"):
                    raise ValueError(f"Unsafe path in tarball: {member.name}")

                # Ensure paths start with data/ or are direct files
                if not (member.name.startswith("data/") or "/" not in member.name):
                    logger.warning(f"Unexpected path in tarball: {member.name}")

            if dry_run:
                logger.info("Would import the following files:")
                for member in members:
                    target_path = project_root / member.name
                    exists = "EXISTS" if target_path.exists() else "NEW"
                    logger.info(f"  {member.name} -> {target_path} ({exists})")
                logger.info("Dry run complete")
                return backup_path

            # Check for conflicts if not overwriting
            conflicts = []
            if not overwrite:
                for member in members:
                    target_path = project_root / member.name
                    if target_path.exists():
                        conflicts.append(str(target_path))

            if conflicts:
                logger.warning(f"Found {len(conflicts)} existing files that would be overwritten:")
                for conflict in conflicts:
                    logger.warning(f"  {conflict}")

                if not overwrite:
                    response = input("Continue and overwrite existing files? [y/N]: ")
                    if response.lower() not in ["y", "yes"]:
                        logger.info("Import cancelled by user")
                        return backup_path

            # Extract files
            logger.info("Extracting files...")
            extracted_count = 0

            for member in members:
                target_path = project_root / member.name

                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    tar.extract(member, path=project_root)
                    extracted_count += 1

                    if verbose:
                        logger.info(f"  Extracted: {member.name}")

                except Exception as e:
                    logger.error(f"Failed to extract {member.name}: {e}")

            logger.info(f"Successfully imported {extracted_count} items")

        return backup_path

    except Exception as e:
        logger.error(f"Failed to import data: {e}")
        raise


def validate_tarball(input_file: str) -> bool:
    """
    Validate that a tarball contains expected data structure.

    Args:
        input_file: Path to tarball to validate

    Returns:
        True if tarball is valid, False otherwise
    """
    logger.info(f"Validating tarball: {input_file}")

    if not Path(input_file).exists():
        logger.error("Tarball file not found")
        return False

    if not tarfile.is_tarfile(input_file):
        logger.error("File is not a valid tarball")
        return False

    try:
        with tarfile.open(input_file, "r:*") as tar:
            members = tar.getmembers()

            if not members:
                logger.warning("Tarball is empty")
                return True

            # Check for unsafe paths
            for member in members:
                if ".." in member.name or member.name.startswith("/"):
                    logger.error(f"Unsafe path in tarball: {member.name}")
                    return False

            logger.info(f"Tarball is valid with {len(members)} items")
            return True

    except Exception as e:
        logger.error(f"Failed to validate tarball: {e}")
        return False


def list_tarball_contents(input_file: str) -> None:
    """
    List the contents of a tarball without extracting.

    Args:
        input_file: Path to tarball to examine
    """
    logger.info(f"Listing contents of: {input_file}")

    if not validate_tarball(input_file):
        return

    try:
        with tarfile.open(input_file, "r:*") as tar:
            members = tar.getmembers()

            if not members:
                logger.info("Tarball is empty")
                return

            total_size = 0
            file_count = 0
            dir_count = 0

            logger.info("Tarball contents:")
            for member in members:
                if member.isfile():
                    file_count += 1
                    total_size += member.size
                    logger.info(f"  FILE: {member.name} ({member.size / (1024 * 1024):.1f} MB)")
                elif member.isdir():
                    dir_count += 1
                    logger.info(f"  DIR:  {member.name}/")
                else:
                    logger.info(f"  ???:  {member.name}")

            logger.info(
                f"Summary: {file_count} files, {dir_count} directories, {total_size / (1024 * 1024):.1f} MB total"
            )

    except Exception as e:
        logger.error(f"Failed to list tarball contents: {e}")

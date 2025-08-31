from pathlib import Path

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


def collect_output_paths() -> set[str]:
    """
    Collect all output paths from the config file.

    Returns:
        Set of resolved output paths
    """
    output_paths: set[str] = set()

    def extract_outputs_recursive(data: dict, path: str = "") -> None:
        """Recursively extract output paths from config data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                if key == "output" or key == "output_dir":
                    # This is an output path
                    if isinstance(value, str):
                        resolved_path = config.expand_variables(value)
                        output_paths.add(resolved_path)
                        logger.debug(f"Found output path: {resolved_path}")
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                resolved_path = config.expand_variables(item)
                                output_paths.add(resolved_path)
                                logger.debug(f"Found output path: {resolved_path}")
                    elif isinstance(value, dict):
                        # Handle output maps like {jsonl: "path1", parquet: "path2"}
                        for format_key, format_path in value.items():
                            if isinstance(format_path, str):
                                resolved_path = config.expand_variables(format_path)
                                output_paths.add(resolved_path)
                                logger.debug(f"Found output path ({format_key}): {resolved_path}")
                elif key == "input" and isinstance(value, list):
                    # Some input lists contain output paths from other steps
                    for item in value:
                        if isinstance(item, str):
                            resolved_path = config.expand_variables(item)
                            # Only include if it looks like an output path (contains base_dir)
                            if resolved_path.startswith(config.get("base_dir", "data")):
                                output_paths.add(resolved_path)
                                logger.debug(
                                    f"Found input path that's also output: {resolved_path}"
                                )
                else:
                    extract_outputs_recursive(value, current_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                extract_outputs_recursive(item, f"{path}[{i}]")

    # Get the full config data
    config_data = config._config
    extract_outputs_recursive(config_data)

    return output_paths


def find_existing_files_and_backups(paths: set[str]) -> dict[str, list[str]]:
    """
    Find existing files/directories and their .bak versions.
    Removes individual files when their parent directories are already included.

    Args:
        paths: Set of paths to check

    Returns:
        Dict mapping original path to list of existing files (including .bak versions)
    """
    existing_files: dict[str, list[str]] = {}
    paths_list = sorted(paths)  # Sort to process parent directories first
    directories_included: set[Path] = set()

    for path_str in paths_list:
        path = Path(path_str)
        files_for_path: list[str] = []

        # Check if this path is already contained within a directory we're including
        skip_path = False
        for included_dir in directories_included:
            try:
                path.resolve().relative_to(included_dir.resolve())
                skip_path = True
                logger.debug(f"Skipping {path_str} - already contained in {included_dir}")
                break
            except ValueError:
                continue

        if skip_path:
            continue

        # Check if the main path exists
        if path.exists():
            files_for_path.append(str(path))
            logger.debug(f"Found existing path: {path}")

            # If this is a directory, remember it to exclude nested files
            if path.is_dir():
                directories_included.add(path)

        # Check for .bak version
        bak_path = Path(f"{path_str}.bak")
        if bak_path.exists():
            files_for_path.append(str(bak_path))
            logger.debug(f"Found backup file: {bak_path}")

        # If it's a directory, also check for .bak directories
        if path.is_dir():
            parent_dir = path.parent
            dir_name = path.name
            bak_dir = parent_dir / f"{dir_name}.bak"
            if bak_dir.exists():
                files_for_path.append(str(bak_dir))
                logger.debug(f"Found backup directory: {bak_dir}")

        if files_for_path:
            existing_files[path_str] = files_for_path

    return existing_files


def get_relative_path_from_root(file_path: str, project_root: str) -> str:
    """
    Get the relative path from project root, ensuring it starts with data/.

    Args:
        file_path: Absolute or relative file path
        project_root: Project root directory

    Returns:
        Relative path from project root
    """
    path = Path(file_path)
    root = Path(project_root)

    try:
        # Try to get relative path from project root
        rel_path = path.relative_to(root)
        return str(rel_path)
    except ValueError:
        # If path is not under project root, make it relative
        # This handles cases where paths might be absolute
        if path.is_absolute():
            # Try to find common ancestor with data directory
            data_dir = root / "data"
            try:
                rel_to_data = path.relative_to(data_dir)
                return f"data/{rel_to_data}"
            except ValueError:
                # Fallback: use just the filename under data/
                return f"data/{path.name}"
        else:
            return str(path)


def create_backup_filename() -> str:
    """
    Create a timestamped backup filename.

    Returns:
        Backup filename with timestamp
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"abzu_data_backup_{timestamp}.tar.gz"

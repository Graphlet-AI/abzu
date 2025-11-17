"""CLI commands for data import/export."""

import click

from abzu.data.export import export_data, list_exportable_data
from abzu.data.import_ import import_data, list_tarball_contents, validate_tarball
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group()
def data() -> None:
    """Data import/export operations."""
    pass


@data.command()
@click.option("--output", "-o", help="Output tarball filename (default: timestamped filename)")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be exported without creating tarball"
)
@click.option("--verbose", "-v", is_flag=True, default=True, help="Enable verbose output")
@click.option("--list-only", is_flag=True, help="List exportable data without creating tarball")
def export(output: str | None, dry_run: bool, verbose: bool, list_only: bool) -> None:
    """
    Export data files defined by output keys in config.yml to a tarball.

    Creates a compressed tarball containing all data files and directories
    specified in the config.yml output paths, including any .bak versions.
    The tarball preserves the data/ directory structure.
    """
    try:
        if list_only:
            list_exportable_data()
            return

        result = export_data(
            output_file=output,
            dry_run=dry_run,
            verbose=verbose,
        )

        if result and not dry_run:
            click.echo(f"Export completed: {result}")
        elif dry_run:
            click.echo("Dry run completed successfully")
        else:
            click.echo("No data found to export")

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise click.ClickException(f"Export failed: {e}")


@data.command("import")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--no-backup", is_flag=True, help="Skip creating backup of existing data")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files without prompting")
@click.option("--dry-run", is_flag=True, help="Show what would be imported without making changes")
@click.option("--verbose", "-v", is_flag=True, default=True, help="Enable verbose output")
def import_command(
    input_file: str, no_backup: bool, overwrite: bool, dry_run: bool, verbose: bool
) -> None:
    """
    Import data from a tarball, creating a backup of existing data first.

    Extracts data from a tarball created by 'abzu data export' and restores
    it to the appropriate locations. By default, creates a backup tarball
    of existing data in the project root before importing.

    INPUT_FILE: Path to the tarball to import
    """
    try:
        # Validate tarball first
        if not validate_tarball(input_file):
            raise click.ClickException("Invalid or corrupted tarball")

        backup_path = import_data(
            input_file=input_file,
            create_backup=not no_backup,
            overwrite=overwrite,
            dry_run=dry_run,
            verbose=verbose,
        )

        if dry_run:
            click.echo("Dry run completed successfully")
        else:
            click.echo("Import completed successfully")
            if backup_path:
                click.echo(f"Backup created: {backup_path}")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise click.ClickException(f"Import failed: {e}")


@data.command()
@click.argument("input_file", type=click.Path(exists=True))
def validate(input_file: str) -> None:
    """
    Validate a data tarball without importing it.

    Checks that the tarball is valid and contains expected data structure.

    INPUT_FILE: Path to the tarball to validate
    """
    try:
        if validate_tarball(input_file):
            click.echo("Tarball is valid")
        else:
            raise click.ClickException("Tarball validation failed")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise click.ClickException(f"Validation failed: {e}")


@data.command()
@click.argument("input_file", type=click.Path(exists=True))
def list(input_file: str) -> None:
    """
    List the contents of a data tarball without extracting it.

    Shows all files and directories contained in the tarball with sizes.

    INPUT_FILE: Path to the tarball to examine
    """
    try:
        list_tarball_contents(input_file)

    except Exception as e:
        logger.error(f"Failed to list tarball contents: {e}")
        raise click.ClickException(f"Failed to list tarball contents: {e}")


if __name__ == "__main__":
    data()

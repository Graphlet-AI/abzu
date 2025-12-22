"""CLI for name similarity-based entity resolution matching."""

import os

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
)
@click.option(
    "--blocks-path",
    "-p",
    default=config.get("process.kg.er.paths.names.blocks"),
    type=click.Path(exists=False, file_okay=True, dir_okay=True),
    help="Path to names blocks file (with {format} placeholder)",
)
@click.option(
    "--output-path",
    "-o",
    default=config.get("process.kg.er.paths.names.matches"),
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    help="Path to save matched entities (with {format} placeholder)",
)
@click.option(
    "--batch-size",
    "-b",
    default=5,
    help="Number of concurrent API calls to make",
)
@click.option(
    "--limit",
    "-n",
    default=None,
    type=int,
    help="Maximum number of blocks to process (for testing)",
)
@click.option(
    "--size-range",
    "-s",
    default=None,
    help="Range of block sizes to process (e.g., 50:100)",
)
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable BAML debug output (shows LLM input/output)",
)
def names(
    iteration: int,
    blocks_path: str,
    output_path: str,
    batch_size: int,
    limit: int | None,
    size_range: str | None,
    debug: bool,
) -> None:
    """Match entities within name similarity-based blocks."""
    # Set BAML log level before importing BAML (must be set before import)
    if not debug:
        os.environ["BAML_LOG"] = "warn"

    # Import after setting env var
    from abzu.er.match import match_entities

    # Parse size range if provided
    min_size = None
    max_size = None
    if size_range:
        try:
            parts = size_range.split(":")
            if len(parts) == 2:
                min_size = int(parts[0])
                max_size = int(parts[1])
                if min_size > max_size:
                    click.echo(
                        f"Error: min size ({min_size}) cannot be greater than max size ({max_size})"
                    )
                    return
            else:
                click.echo(
                    f"Error: Invalid size range format '{size_range}'. Use format like '50:100'"
                )
                return
        except ValueError:
            click.echo(
                f"Error: Invalid size range '{size_range}'. Must be integers in format 'min:max'"
            )
            return

    try:
        match_entities(
            blocks_path=blocks_path,
            output_path=output_path,
            iteration=iteration,
            batch_size=batch_size,
            limit=limit,
            min_block_size=min_size,
            max_block_size=max_size,
        )
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise click.exceptions.Exit(1)

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
    "--strategy",
    "-s",
    required=True,
    type=click.Choice(["first_word", "acronym", "combined"]),
    help="Blocking strategy to match (must match the strategy used in blocking)",
)
@click.option(
    "--blocks-path",
    "-p",
    default=None,
    type=click.Path(exists=False, file_okay=True, dir_okay=True),
    help="Path to names blocks file (defaults to strategy-specific path)",
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
    "-r",
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
    strategy: str,
    blocks_path: str | None,
    output_path: str,
    batch_size: int,
    limit: int | None,
    size_range: str | None,
    debug: bool,
) -> None:
    """Match entities within name similarity-based blocks.

    The strategy must match the one used in the blocking step.
    """
    # Set BAML log level before importing BAML (must be set before import)
    if not debug:
        os.environ["BAML_LOG"] = "warn"

    # Import after setting env var
    from abzu.er.match import match_entities

    # Set blocks_path based on strategy if not provided
    if blocks_path is None:
        blocks_dir = config.get("process.kg.er.paths.names.blocks_dir").format(iteration=iteration)
        blocks_path = os.path.join(blocks_dir, f"{strategy}_blocks.parquet")

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

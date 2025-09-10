"""CLI for name similarity-based entity resolution matching."""

import click

from abzu.config import config
from abzu.er.match import match_entities


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
    default=None,
    help="Path to names blocks parquet file (overrides config)",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    help="Path to save matched entities (overrides config)",
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
def names(
    iteration: int,
    blocks_path: str | None,
    output_path: str | None,
    batch_size: int,
    limit: int | None,
    size_range: str | None,
) -> None:
    """Match entities within name similarity-based blocks."""
    # Use config paths if not overridden
    if blocks_path is None:
        blocks_path = config.get("process.kg.er.paths.names.blocks").replace(
            "{iteration}", str(iteration)
        )
    if output_path is None:
        output_path = config.get("process.kg.er.paths.names.matches").replace(
            "{iteration}", str(iteration)
        )

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

    match_entities(
        blocks_path=blocks_path,
        output_path=output_path,
        batch_size=batch_size,
        limit=limit,
        min_block_size=min_size,
        max_block_size=max_size,
    )

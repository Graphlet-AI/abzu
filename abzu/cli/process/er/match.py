"""CLI for entity resolution matching."""

import click

from abzu.config import config
from abzu.er.match import match_entities


@click.command(context_settings={"show_default": True})
@click.option(
    "--blocks-path",
    default=config.get("er.paths.blocks", "data/er/all_blocks.parquet"),
    help="Path to blocks parquet file",
)
@click.option(
    "--output-path",
    "-o",
    default=config.get("er.paths.matches", "data/er/matches.parquet"),
    help="Path to save matched entities",
)
@click.option(
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
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
def match(
    blocks_path: str,
    output_path: str,
    iteration: int,
    batch_size: int,
    limit: int | None,
    size_range: str | None,
) -> None:
    """Match entities within blocks using similarity metrics."""
    # Override paths based on iteration
    if not blocks_path.startswith("data/er/iterations/"):
        blocks_path = f"data/er/iterations/{iteration}/all_blocks.parquet"
    if not output_path.startswith("data/er/iterations/"):
        output_path = f"data/er/iterations/{iteration}/matches.parquet"

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

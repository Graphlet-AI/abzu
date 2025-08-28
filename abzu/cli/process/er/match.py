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
def match(
    blocks_path: str,
    output_path: str,
    batch_size: int,
    limit: int | None,
) -> None:
    """Match entities within blocks using similarity metrics."""
    match_entities(
        blocks_path=blocks_path,
        output_path=output_path,
        batch_size=batch_size,
        limit=limit,
    )

"""CLI for entity resolution matching."""

import click

from abzu.config import config
from abzu.er.match import match_entities


@click.command(context_settings={"show_default": True})
@click.option(
    "--blocks-path",
    "-b",
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
    "--local-mode/--no-local-mode",
    default=None,
    help="Force local mode for Spark session",
)
def match(
    blocks_path: str,
    output_path: str,
    local_mode: bool | None,
) -> None:
    """Match entities within blocks using similarity metrics."""
    match_entities(
        blocks_path=blocks_path,
        output_path=output_path,
        local_mode=local_mode,
    )

"""CLI for entity resolution blocking analysis."""

import click

from abzu.config import config
from abzu.spark.er_graph import build_blocks


@click.command(context_settings={"show_default": True})
@click.option(
    "--companies-path",
    "-c",
    default=config.get("process.kg.er.companies_path", "data/knowledge_graph/companies.parquet"),
    help="Path to companies parquet file",
)
@click.option(
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
)
@click.option(
    "--local-mode/--no-local-mode",
    default=None,
    help="Force local mode for Spark session",
)
def block(companies_path: str, iteration: int, local_mode: bool | None) -> None:
    """Analyze company entity resolution blocking strategies."""
    # For iterations > 1, use the resolved companies from previous iteration
    if iteration > 1:
        companies_path = f"data/er/iterations/{iteration - 1}/companies_resolved.parquet"

    # Set output path based on iteration
    output_path = f"data/er/iterations/{iteration}"

    build_blocks(
        companies_path=companies_path,
        output_path=output_path,
        local_mode=local_mode,
    )

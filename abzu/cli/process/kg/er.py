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
    "--local-mode/--no-local-mode",
    default=None,
    help="Force local mode for Spark session",
)
def er(companies_path: str, local_mode: bool | None) -> None:
    """Analyze company entity resolution blocking strategies."""
    build_blocks(
        companies_path=companies_path,
        local_mode=local_mode,
    )

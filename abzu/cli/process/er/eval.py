"""CLI for entity resolution evaluation."""

import os

import click

from abzu.config import config
from abzu.spark.er_match import evaluate_er_matches


@click.command(context_settings={"show_default": True})
@click.option(
    "--matches-path",
    default=config.get("process.kg.er.paths.matches", "data/er/matches.parquet"),
    help="Path to matches parquet file",
)
@click.option(
    "--raw-companies-path",
    default=os.path.join(config.get("process.kg.raw.output"), "companies.parquet"),
    help="Path to raw companies parquet file (unmerged records)",
)
@click.option(
    "--output-path",
    "-o",
    default=config.get("process.kg.er.paths.eval", "data/er/"),
    help="Directory path to save evaluation results",
)
@click.option(
    "--local-mode",
    is_flag=True,
    help="Force local Spark mode instead of distributed",
)
def eval(
    matches_path: str,
    raw_companies_path: str,
    output_path: str,
    local_mode: bool,
) -> None:
    """Evaluate entity resolution matches by exploding companies and validating source UUIDs."""
    evaluate_er_matches(
        matches_path=matches_path,
        raw_companies_path=raw_companies_path,
        output_path=output_path,
        local_mode=local_mode if local_mode else None,
    )

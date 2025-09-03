"""CLI for entity resolution evaluation."""

import os

import click

from abzu.config import config
from abzu.spark.er_eval import evaluate_er_matches


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
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
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
    iteration: int,
    local_mode: bool,
) -> None:
    """Evaluate entity resolution matches by exploding companies and validating source UUIDs."""
    # Override paths based on iteration
    if not matches_path.startswith("data/er/iterations/"):
        matches_path = f"data/er/iterations/{iteration}/matches.parquet"
    if not output_path.startswith("data/er/iterations/"):
        output_path = f"data/er/iterations/{iteration}"

    # For iteration 1, use the original raw companies
    # For iteration > 1, use companies from iteration 0 (or original raw companies)
    if iteration == 1 and not raw_companies_path.startswith("data/er/iterations/"):
        # Use default raw companies path
        pass
    elif iteration > 1:
        # For subsequent iterations, compare against the original raw companies
        raw_companies_path = os.path.join(config.get("process.kg.raw.output"), "companies.parquet")

    evaluate_er_matches(
        matches_path=matches_path,
        raw_companies_path=raw_companies_path,
        output_path=output_path,
        local_mode=local_mode if local_mode else None,
    )

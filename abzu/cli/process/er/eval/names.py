"""CLI for name similarity-based entity resolution evaluation."""

import click

from abzu.config import config
from abzu.spark.er_eval import evaluate_er_matches


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
)
@click.option(
    "--matches-path",
    "-m",
    default=None,
    help="Path to names matches parquet file (overrides config)",
)
@click.option(
    "--raw-companies-path",
    "-r",
    default=None,
    help="Path to raw companies parquet file (overrides config)",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    help="Directory path to save evaluation results (overrides config)",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local mode",
)
def names(
    iteration: int,
    matches_path: str | None,
    raw_companies_path: str | None,
    output_path: str | None,
    local_mode: bool,
) -> None:
    """Evaluate name similarity-based entity resolution matches."""
    # Use config paths if not overridden
    if matches_path is None:
        matches_path = config.get("process.kg.er.paths.names.matches").replace(
            "{iteration}", str(iteration)
        )
    if raw_companies_path is None:
        # Always use raw companies from knowledge graph as baseline for comparison
        raw_companies_path = config.get("process.kg.er.paths.input")
    if output_path is None:
        output_path = config.get("process.kg.er.paths.names.eval").replace(
            "{iteration}", str(iteration)
        )

    evaluate_er_matches(
        matches_path=matches_path,
        raw_companies_path=raw_companies_path,
        output_path=output_path,
        local_mode=local_mode if local_mode else None,
    )

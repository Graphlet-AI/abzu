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
    default=config.get("process.kg.er.paths.names.matches"),
    type=click.Path(exists=False, file_okay=True, dir_okay=True),
    help="Path to names matches file (with {format} placeholder)",
)
@click.option(
    "--raw-companies-path",
    "-r",
    default=config.get("process.kg.er.paths.input"),
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Path to raw companies parquet file",
)
@click.option(
    "--output-path",
    "-o",
    default=config.get("process.kg.er.paths.names.eval"),
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    help="Path to save evaluation results (with {format} placeholder)",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local mode",
)
def names(
    iteration: int,
    matches_path: str,
    raw_companies_path: str,
    output_path: str,
    local_mode: bool,
) -> None:
    """Evaluate name similarity-based entity resolution matches."""

    evaluate_er_matches(
        matches_path=matches_path,
        raw_companies_path=raw_companies_path,
        output_path=output_path,
        iteration=iteration,
        local_mode=local_mode if local_mode else None,
    )

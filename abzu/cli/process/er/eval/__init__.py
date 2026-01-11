"""CLI for entity resolution evaluation."""

import click

from abzu.config import config


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
    help="Path to matches.jsonl file from match step",
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
    help="Path to save evaluation results",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local mode",
)
def eval(
    iteration: int,
    matches_path: str,
    raw_companies_path: str,
    output_path: str,
    local_mode: bool,
) -> None:
    """Evaluate entity resolution matches.

    Validates matching results, tracks UUID lineage, and ensures no data loss.
    Works with any blocking method (name-based, semantic, or combined).
    """
    # Import heavy Spark module only when command is executed
    from abzu.spark.er_eval import evaluate_er_matches

    try:
        evaluate_er_matches(
            matches_path=matches_path,
            raw_companies_path=raw_companies_path,
            output_path=output_path,
            iteration=iteration,
            local_mode=local_mode if local_mode else None,
        )
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise click.exceptions.Exit(1)

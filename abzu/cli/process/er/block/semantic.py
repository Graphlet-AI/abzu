"""CLI for semantic embedding-based entity resolution blocking."""

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
    "--companies-path",
    "-c",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Path to companies parquet file or directory (defaults to config path)",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Path to save semantic blocks directory (defaults to config path with iteration)",
)
@click.option(
    "--target-block-size",
    "-t",
    default=50,
    type=int,
    help="Target average number of companies per block",
)
@click.option(
    "--max-distance",
    "-d",
    default=0.01,
    type=float,
    help="Maximum distance threshold for clustering",
)
@click.option(
    "--batch-size",
    "-b",
    default=64,
    type=int,
    help="Batch size for embedding computation",
)
def semantic(
    iteration: int,
    companies_path: str | None,
    output_path: str | None,
    target_block_size: int,
    max_distance: float,
    batch_size: int,
) -> None:
    """Build semantic embedding-based blocks for entity resolution.

    Uses KMeans clustering on E5-large-instruct embeddings to group
    semantically similar company names into blocks.

    This is typically used as a second stage after heuristic blocking
    to catch matches that name-based strategies miss.
    """
    from abzu.spark.er_block_semantic import build_semantic_blocks

    # Handle iteration-based paths
    if companies_path is None:
        if iteration > 1:
            # For later iterations, use previous iteration's resolved companies
            prev_iteration = iteration - 1
            companies_path = config.get("process.kg.er.paths.names.eval").format(
                iteration=prev_iteration
            )
        else:
            companies_path = config.get("process.kg.er.paths.input")

    # Set output path if not provided
    if output_path is None:
        output_path = config.get("process.kg.er.paths.names.blocks_dir").format(iteration=iteration)

    try:
        build_semantic_blocks(
            input_path=companies_path,
            output_path=output_path,
            target_block_size=target_block_size,
            max_distance=max_distance,
            batch_size=batch_size,
        )
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise click.exceptions.Exit(1)

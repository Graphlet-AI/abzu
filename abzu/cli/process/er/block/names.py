"""CLI for name similarity-based entity resolution blocking."""

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
    default=config.get("process.kg.er.paths.input"),
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Path to companies parquet file or directory",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Path to save name blocks directory (defaults to config path with iteration)",
)
@click.option(
    "--max-block-size",
    "-m",
    default=50,
    type=int,
    help="Maximum block size (blocks larger than this will be chunked)",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local mode",
)
def names(
    iteration: int,
    companies_path: str,
    output_path: str | None,
    max_block_size: int,
    local_mode: bool,
) -> None:
    """Build name similarity-based blocks for entity resolution."""
    # Import heavy Spark module only when command is executed
    from abzu.spark.er_block import build_blocks

    # Handle iteration-based paths
    if iteration > 1:
        # For later iterations, use previous iteration's resolved companies
        prev_iteration = iteration - 1
        companies_path = config.get("process.kg.er.paths.names.eval").format(
            iteration=prev_iteration, format="parquet"
        )

    # Set output path if not provided
    if output_path is None:
        output_path = config.get("process.kg.er.paths.names.blocks_dir").format(iteration=iteration)

    # Note: max_block_size is configured via config.yml, not passed as parameter
    # The build_blocks function will use the configured value
    build_blocks(
        input_path=companies_path,
        output_path=output_path,
        local_mode=local_mode if local_mode else None,
    )

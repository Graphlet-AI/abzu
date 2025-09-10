"""CLI for name similarity-based entity resolution blocking."""

import click

from abzu.config import config
from abzu.spark.er_block import build_blocks


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
    help="Path to companies parquet file (overrides config)",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    help="Path to save name blocks (overrides config)",
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
    companies_path: str | None,
    output_path: str | None,
    max_block_size: int,
    local_mode: bool,
) -> None:
    """Build name similarity-based blocks for entity resolution."""
    # Use config paths if not overridden
    if companies_path is None:
        # For iteration 1, use raw companies from knowledge graph
        # For later iterations, use previous iteration's resolved companies
        if iteration == 1:
            companies_path = config.get("process.kg.er.paths.input")
        else:
            prev_iteration = iteration - 1
            companies_path = (
                config.get("process.kg.er.paths.names.eval").replace(
                    "{iteration}", str(prev_iteration)
                )
                + "companies_resolved.parquet"
            )

    if output_path is None:
        output_path = config.get("process.kg.er.paths.names.blocks").replace(
            "{iteration}", str(iteration)
        )

    # Note: max_block_size is configured via config.yml, not passed as parameter
    # The build_blocks function will use the configured value
    build_blocks(
        input_path=companies_path,
        output_path=output_path,
        use_uuid_blocks=False,  # We're not using UUID blocks anymore
        local_mode=local_mode if local_mode else None,
    )

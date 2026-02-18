"""CLI for entity resolution matching."""

import os
from pathlib import Path

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
    "--blocks-dir",
    "-d",
    default=None,
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help="Directory containing block parquet files (loads all *_blocks.parquet files)",
)
@click.option(
    "--output-path",
    "-o",
    default=None,
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    help="Path to save matched entities",
)
@click.option(
    "--batch-size",
    "-b",
    default=5,
    help="Number of concurrent API calls to make",
)
@click.option(
    "--limit",
    "-n",
    default=None,
    type=int,
    help="Maximum number of blocks to process (for testing)",
)
@click.option(
    "--size-range",
    "-s",
    default=None,
    help="Range of block sizes to process (e.g., 50:100)",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable BAML debug output (shows LLM input/output)",
)
@click.option(
    "--name-blocks-only",
    is_flag=True,
    help="Only use name-based blocks (union_blocks.parquet), ignore semantic blocks",
)
@click.option(
    "--semantic-blocks-only",
    is_flag=True,
    help="Only use semantic blocks (semantic_blocks.parquet), ignore name-based blocks",
)
def match(
    iteration: int,
    blocks_dir: str | None,
    output_path: str | None,
    batch_size: int,
    limit: int | None,
    size_range: str | None,
    debug: bool,
    name_blocks_only: bool,
    semantic_blocks_only: bool,
) -> None:
    """Match entities within blocks using BAML/LLM.

    By default, loads both name-based blocks (union_blocks.parquet) and
    semantic blocks (semantic_blocks.parquet) if they exist, combining
    them for matching.

    Use --name-blocks-only or --semantic-blocks-only to match against
    only one type of blocks.
    """
    # Set BAML log level before importing BAML (must be set before import)
    if not debug:
        os.environ["BAML_LOG"] = "warn"

    # Import after setting env var
    from abzu.er.match import match_entities
    from abzu.logs import get_logger
    from abzu.spark.config import get_spark_session

    logger = get_logger(__name__)

    # Validate mutual exclusivity
    if name_blocks_only and semantic_blocks_only:
        click.echo("Error: Cannot use both --name-blocks-only and --semantic-blocks-only")
        raise click.exceptions.Exit(1)

    # Set default paths based on iteration
    if blocks_dir is None:
        blocks_dir = config.get("process.kg.er.paths.blocks_dir").format(iteration=iteration)

    if output_path is None:
        output_path = config.get("process.kg.er.paths.matches").format(iteration=iteration)

    # Parse size range if provided
    min_size = None
    max_size = None
    if size_range:
        try:
            parts = size_range.split(":")
            if len(parts) == 2:
                min_size = int(parts[0])
                max_size = int(parts[1])
                if min_size > max_size:
                    click.echo(
                        f"Error: min size ({min_size}) cannot be greater than max size ({max_size})"
                    )
                    return
            else:
                click.echo(
                    f"Error: Invalid size range format '{size_range}'. Use format like '50:100'"
                )
                return
        except ValueError:
            click.echo(
                f"Error: Invalid size range '{size_range}'. Must be integers in format 'min:max'"
            )
            return

    # Determine which block files to load
    blocks_dir_path = Path(blocks_dir)
    name_blocks_path = blocks_dir_path / "union_blocks.parquet"
    semantic_blocks_path = blocks_dir_path / "semantic_blocks.parquet"

    blocks_to_load = []

    if name_blocks_only:
        if name_blocks_path.exists():
            blocks_to_load.append(str(name_blocks_path))
        else:
            click.echo(f"Error: Name blocks not found at {name_blocks_path}")
            raise click.exceptions.Exit(1)
    elif semantic_blocks_only:
        if semantic_blocks_path.exists():
            blocks_to_load.append(str(semantic_blocks_path))
        else:
            click.echo(f"Error: Semantic blocks not found at {semantic_blocks_path}")
            raise click.exceptions.Exit(1)
    else:
        # Load both if they exist
        if name_blocks_path.exists():
            blocks_to_load.append(str(name_blocks_path))
        if semantic_blocks_path.exists():
            blocks_to_load.append(str(semantic_blocks_path))

    if not blocks_to_load:
        click.echo(
            f"Error: No block files found in {blocks_dir}\n\n"
            f"Please run blocking first:\n"
            f"  abzu process er block names --iteration {iteration}\n"
            f"  abzu process er block semantic --iteration {iteration}\n\n"
            f"Or run the complete pipeline:\n"
            f"  abzu process er all --iteration {iteration}"
        )
        raise click.exceptions.Exit(1)

    # Log what we're loading
    logger.info(f"Loading blocks from {len(blocks_to_load)} file(s):")
    for path in blocks_to_load:
        logger.info(f"  - {path}")

    # If we have multiple block files, combine them
    if len(blocks_to_load) > 1:
        logger.info("Combining multiple block files...")

        # Create Spark session to combine blocks
        spark = get_spark_session("CombineBlocks")

        # Load and union all block files
        combined_df = None
        for block_path in blocks_to_load:
            df = spark.read.parquet(block_path)
            if combined_df is None:
                combined_df = df
            else:
                combined_df = combined_df.union(df)

        # Save combined blocks to a temporary file
        combined_blocks_path = str(blocks_dir_path / "combined_blocks.parquet")
        logger.info(f"Saving combined blocks to {combined_blocks_path}")
        if combined_df is not None:
            combined_df.write.mode("overwrite").parquet(combined_blocks_path)

        # Use the combined file for matching
        final_blocks_path = combined_blocks_path
        spark.stop()
    else:
        final_blocks_path = blocks_to_load[0]

    try:
        match_entities(
            blocks_path=final_blocks_path,
            output_path=output_path,
            iteration=iteration,
            batch_size=batch_size,
            limit=limit,
            min_block_size=min_size,
            max_block_size=max_size,
        )
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        raise click.exceptions.Exit(1)

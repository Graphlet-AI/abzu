"""CLI for final entity resolution deduplication."""

import click

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    "-i",
    required=True,
    type=int,
    help="Iteration number to process",
)
@click.option(
    "--output-path",
    "-o",
    default=config.get("process.kg.er.paths.names.final"),
    type=str,
    help="Path to output final companies file (with {iteration} placeholder)",
)
@click.option(
    "--batch-size",
    "-b",
    default=5,
    type=int,
    help="Batch size for concurrent BAML calls",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local Spark mode",
)
def final(
    iteration: int,
    output_path: str,
    batch_size: int,
    local_mode: bool,
) -> None:
    """Deduplicate resolved companies by grouping on UUID and merging with BAML.

    This command reads the matches output from an iteration, groups companies
    by UUID to find duplicates, and uses BAML's FinalEntityResolution to
    intelligently merge duplicate records into single, high-quality companies.

    The output is written to companies_final.json in the same iteration directory.
    """
    from abzu.spark.er_final import deduplicate_resolved_companies

    # Format paths with iteration
    matches_path = config.get("process.kg.er.paths.names.matches").format(iteration=iteration)
    final_path = output_path.format(iteration=iteration)

    click.echo(f"Final deduplication for iteration {iteration}")
    click.echo(f"Input:  {matches_path}")
    click.echo(f"Output: {final_path}")
    click.echo()

    try:
        metrics = deduplicate_resolved_companies(
            matches_path=matches_path,
            output_path=final_path,
            uuid_blocks_path=config.get("process.kg.er.paths.names.uuid_blocks").format(
                iteration=iteration
            ),
            uuid_matches_path=config.get("process.kg.er.paths.names.uuid_matches").format(
                iteration=iteration
            ),
            iteration=iteration,
            batch_size=batch_size,
            local_mode=local_mode if local_mode else None,
        )

        # Display results
        click.echo()
        click.echo("✓ Deduplication completed")
        click.echo(f"  • Input records:       {metrics['input_count']:,}")
        click.echo(f"  • Duplicate records:   {metrics['duplicate_count']:,}")
        click.echo(f"  • Output records:      {metrics['output_count']:,}")
        if metrics["input_count"] > 0:
            reduction_pct = metrics["duplicate_count"] / metrics["input_count"] * 100
            click.echo(f"  • Reduction:           {reduction_pct:.2f}%")
        click.echo()
        click.echo(f"Output saved to: {final_path}")

    except Exception as e:
        click.echo(f"✗ Final deduplication failed: {e}", err=True)
        raise

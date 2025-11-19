"""CLI for running complete entity resolution cycle (block, match, eval)."""

import json
import time
from datetime import timedelta
from pathlib import Path

import click
import pandas as pd

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


def get_blocking_metrics(input_path: str, blocks_path: str) -> dict[str, int]:
    """Extract key metrics from blocking stage output."""
    try:
        # Read input companies - handle both file and Spark directory
        input_path_obj = Path(input_path)
        if input_path_obj.is_dir():
            # Spark directory - read all part files
            part_files = list(input_path_obj.glob("part-*.json"))
            if part_files:
                input_df = pd.concat([pd.read_json(f, lines=True) for f in part_files])
            else:
                return {"input_companies": 0, "blocks_created": 0, "largest_block": 0}
        else:
            input_df = pd.read_json(input_path, lines=True)
        input_count = len(input_df)

        # Read blocks - handle both file and Spark directory
        blocks_path_obj = Path(blocks_path)
        if blocks_path_obj.is_dir():
            # Spark directory - read all part files
            part_files = list(blocks_path_obj.glob("part-*.json"))
            if part_files:
                blocks_df = pd.concat([pd.read_json(f, lines=True) for f in part_files])
            else:
                return {"input_companies": input_count, "blocks_created": 0, "largest_block": 0}
        else:
            blocks_df = pd.read_json(blocks_path, lines=True)
        blocks_count = len(blocks_df)

        # Get largest block size
        largest_block = blocks_df["block_size"].max() if "block_size" in blocks_df.columns else 0

        return {
            "input_companies": input_count,
            "blocks_created": blocks_count,
            "largest_block": largest_block,
        }
    except Exception as e:
        logger.warning(f"Could not extract blocking metrics: {e}")
        return {"input_companies": 0, "blocks_created": 0, "largest_block": 0}


def get_matching_metrics(matches_path: str) -> dict[str, int]:
    """Extract key metrics from matching stage output."""
    try:
        # Read matches - handle both file and Spark directory
        matches_path_obj = Path(matches_path)
        if matches_path_obj.is_dir():
            # Spark directory - read all part files
            part_files = list(matches_path_obj.glob("part-*.json"))
            if part_files:
                matches_df = pd.concat([pd.read_json(f, lines=True) for f in part_files])
            else:
                return {"blocks_processed": 0, "total_companies": 0, "skipped": 0}
        else:
            matches_df = pd.read_json(matches_path, lines=True)
        blocks_processed = len(matches_df)

        # Explode resolved companies to count them
        resolved_companies = []
        for _, row in matches_df.iterrows():
            companies = row.get("resolved_companies", [])
            if isinstance(companies, list):
                resolved_companies.extend(companies)

        total_companies = len(resolved_companies)

        # Count skipped/singletons
        skipped = sum(
            1 for c in resolved_companies if isinstance(c, dict) and c.get("match_skip") is True
        )

        return {
            "blocks_processed": blocks_processed,
            "total_companies": total_companies,
            "skipped": skipped,
        }
    except Exception as e:
        logger.warning(f"Could not extract matching metrics: {e}")
        return {"blocks_processed": 0, "total_companies": 0, "skipped": 0}


def get_evaluation_metrics(eval_path: str, metrics_path: str) -> dict[str, int | float]:
    """Extract key metrics from evaluation stage output."""
    try:
        # Try to read the metrics JSON file first (more accurate)
        metrics_path_obj = Path(metrics_path)
        if metrics_path_obj.exists():
            if metrics_path_obj.is_dir():
                # Spark directory - read part file
                part_files = sorted(list(metrics_path_obj.glob("part-*.json")))
                if part_files:
                    with open(part_files[0]) as f:
                        metrics = json.load(f)
                else:
                    raise FileNotFoundError("No part files in metrics directory")
            else:
                # Single file
                with open(metrics_path) as f:
                    metrics = json.load(f)

            return {
                "original_companies": metrics.get("total_original_companies", 0),
                "final_companies": metrics.get("total_output_companies", 0),
                "reduction_pct": metrics.get("total_reduction_pct", 0.0),
            }

        # Fallback: read the resolved companies file
        eval_path_obj = Path(eval_path)
        if eval_path_obj.is_dir():
            # Spark directory - read all part files
            part_files = list(eval_path_obj.glob("part-*.json"))
            if part_files:
                eval_df = pd.concat([pd.read_json(f, lines=True) for f in part_files])
            else:
                return {"original_companies": 0, "final_companies": 0, "reduction_pct": 0.0}
        else:
            eval_df = pd.read_json(eval_path, lines=True)
        final_count = len(eval_df)

        return {
            "original_companies": 0,
            "final_companies": final_count,
            "reduction_pct": 0.0,
        }
    except Exception as e:
        logger.warning(f"Could not extract evaluation metrics: {e}")
        return {"original_companies": 0, "final_companies": 0, "reduction_pct": 0.0}


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    "-i",
    default=1,
    type=int,
    help="Iteration number for multi-round ER processing",
)
@click.option(
    "--max-block-size",
    "-m",
    default=50,
    type=int,
    help="Maximum block size for blocking step",
)
@click.option(
    "--batch-size",
    "-b",
    default=5,
    type=int,
    help="Batch size for concurrent API calls in matching step",
)
@click.option(
    "--local-mode",
    "-l",
    is_flag=True,
    help="Run in local mode",
)
def all(
    iteration: int,
    max_block_size: int,
    batch_size: int,
    local_mode: bool,
) -> None:
    """Run complete entity resolution cycle: block, match, and evaluate.

    This command orchestrates the full ER pipeline:
    1. Block: Create similarity-based blocks of companies
    2. Match: Resolve entities within blocks using BAML
    3. Eval: Evaluate results and generate metrics

    At the end, prints a comprehensive report of the entire cycle.
    """
    from abzu.er.match import match_entities
    from abzu.spark.er_block import build_blocks
    from abzu.spark.er_eval import evaluate_er_matches

    cycle_start = time.time()

    # Print header
    click.echo("=" * 80)
    click.echo(f"ENTITY RESOLUTION CYCLE - ITERATION {iteration}")
    click.echo("=" * 80)
    click.echo()

    # Configure paths based on iteration
    if iteration > 1:
        # For later iterations, use previous iteration's resolved companies
        prev_iteration = iteration - 1
        companies_path = config.get("process.kg.er.paths.names.eval").format(
            iteration=prev_iteration, format="json"
        )
    else:
        companies_path = config.get("process.kg.er.paths.input")

    blocks_dir = config.get("process.kg.er.paths.names.blocks_dir").format(iteration=iteration)
    blocks_path = config.get("process.kg.er.paths.names.blocks").format(
        iteration=iteration, format="json"
    )
    matches_path = config.get("process.kg.er.paths.names.matches").format(
        iteration=iteration, format="json"
    )
    eval_path = config.get("process.kg.er.paths.names.eval").format(
        iteration=iteration, format="json"
    )

    # Step 1: Blocking
    click.echo(f"[1/3] BLOCKING (max_block_size={max_block_size})")
    click.echo("-" * 80)
    block_start = time.time()

    try:
        build_blocks(
            input_path=companies_path,
            output_path=blocks_dir,
            local_mode=local_mode if local_mode else None,
            max_block_size=max_block_size,
        )
        block_time = time.time() - block_start

        # Extract and display blocking metrics
        block_metrics = get_blocking_metrics(companies_path, blocks_path)
        click.echo(f"✓ Blocking completed in {timedelta(seconds=int(block_time))}")
        click.echo(f"  • Input companies: {block_metrics['input_companies']:,}")
        click.echo(f"  • Blocks created: {block_metrics['blocks_created']:,}")
        click.echo(f"  • Largest block: {block_metrics['largest_block']:,}")
        click.echo()
    except Exception as e:
        click.echo(f"✗ Blocking failed: {e}", err=True)
        return

    # Step 2: Matching
    click.echo(f"[2/3] MATCHING (batch_size={batch_size})")
    click.echo("-" * 80)
    match_start = time.time()

    try:
        match_entities(
            blocks_path=blocks_path,
            output_path=matches_path,
            iteration=iteration,
            batch_size=batch_size,
            limit=None,
            min_block_size=None,
            max_block_size=None,
        )
        match_time = time.time() - match_start

        # Extract and display matching metrics
        match_metrics = get_matching_metrics(matches_path)
        click.echo(f"✓ Matching completed in {timedelta(seconds=int(match_time))}")
        click.echo(f"  • Blocks processed: {match_metrics['blocks_processed']:,}")
        click.echo(f"  • Companies in output: {match_metrics['total_companies']:,}")
        click.echo(f"  • Skipped/singletons: {match_metrics['skipped']:,}")
        click.echo()
    except Exception as e:
        click.echo(f"✗ Matching failed: {e}", err=True)
        return

    # Step 3: Evaluation
    click.echo("[3/3] EVALUATION")
    click.echo("-" * 80)
    eval_start = time.time()

    try:
        evaluate_er_matches(
            matches_path=matches_path,
            raw_companies_path=config.get("process.kg.er.paths.input"),
            output_path=eval_path,
            iteration=iteration,
            local_mode=local_mode if local_mode else None,
        )
        eval_time = time.time() - eval_start

        # Extract and display evaluation metrics
        eval_dir = str(Path(eval_path).parent)
        metrics_path = str(Path(eval_dir) / "er_evaluation_metrics.json")
        eval_metrics = get_evaluation_metrics(eval_path, metrics_path)
        click.echo(f"✓ Evaluation completed in {timedelta(seconds=int(eval_time))}")
        click.echo(f"  • Original companies: {eval_metrics['original_companies']:,}")
        click.echo(f"  • Final companies: {eval_metrics['final_companies']:,}")
        click.echo(f"  • Total reduction: {eval_metrics['reduction_pct']:.2f}%")
        click.echo()
    except Exception as e:
        click.echo(f"✗ Evaluation failed: {e}", err=True)
        return

    # Print overall summary
    cycle_time = time.time() - cycle_start
    click.echo("=" * 80)
    click.echo("CYCLE SUMMARY")
    click.echo("=" * 80)
    click.echo(f"Iteration: {iteration}")
    click.echo(f"Total time: {timedelta(seconds=int(cycle_time))}")
    click.echo()
    click.echo("Overall pipeline:")
    click.echo(
        f"  {eval_metrics['original_companies']:,} companies → "
        f"{eval_metrics['final_companies']:,} companies "
        f"({eval_metrics['reduction_pct']:.2f}% reduction)"
    )
    click.echo()
    click.echo("Step timing breakdown:")
    click.echo(f"  1. Blocking:    {timedelta(seconds=int(block_time))}")
    click.echo(f"  2. Matching:    {timedelta(seconds=int(match_time))}")
    click.echo(f"  3. Evaluation:  {timedelta(seconds=int(eval_time))}")
    click.echo()
    click.echo("Output files:")
    click.echo(f"  - Blocks:      {blocks_path}")
    click.echo(f"  - Matches:     {matches_path}")
    click.echo(f"  - Resolved:    {eval_path}")
    click.echo(f"  - Metrics:     {metrics_path}")
    click.echo()
    click.echo("✓ Entity resolution cycle completed successfully!")
    click.echo("=" * 80)

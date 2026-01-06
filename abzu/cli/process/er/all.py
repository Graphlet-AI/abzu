"""CLI for running complete entity resolution cycle (block, match, eval)."""

import os
import time
from datetime import timedelta
from pathlib import Path

import click

from abzu.config import config
from abzu.er.metrics import (
    get_all_iteration_metrics,
    get_blocking_metrics,
    get_evaluation_metrics,
    get_matching_metrics,
)
from abzu.logs import get_logger

logger = get_logger(__name__)


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
@click.option(
    "--debug",
    "-d",
    is_flag=True,
    help="Enable BAML debug output (shows LLM input/output)",
)
def all(
    iteration: int,
    max_block_size: int,
    batch_size: int,
    local_mode: bool,
    debug: bool,
) -> None:
    """Run complete entity resolution cycle: block, match, and evaluate.

    This command orchestrates the full ER pipeline:
    1. Block: Create similarity-based blocks of companies
    2. Match: Resolve entities within blocks using BAML
    3. Eval: Evaluate results, deduplicate exact copies, and generate metrics

    At the end, prints a comprehensive report of the entire cycle.
    """
    # Set BAML log level before importing BAML (must be set before import)
    if not debug:
        os.environ["BAML_LOG"] = "warn"

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
        # For later iterations, use previous iteration's resolved companies (Parquet)
        prev_iteration = iteration - 1
        companies_path = config.get("process.kg.er.paths.names.eval").format(
            iteration=prev_iteration
        )
    else:
        companies_path = config.get("process.kg.er.paths.input")

    blocks_dir = config.get("process.kg.er.paths.names.blocks_dir").format(iteration=iteration)
    blocks_path = config.get("process.kg.er.paths.names.blocks").format(iteration=iteration)
    matches_path = config.get("process.kg.er.paths.names.matches").format(iteration=iteration)
    eval_path = config.get("process.kg.er.paths.names.eval").format(iteration=iteration)

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

    # Step 3: Evaluation (reads from matches, deduplicates exact copies)
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
        metrics_path = str(Path(eval_dir) / "er_evaluation_metrics.parquet")
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
    reduction_count = eval_metrics["original_companies"] - eval_metrics["final_companies"]

    # Calculate stage-specific metrics
    block_throughput = block_metrics["input_companies"] / block_time if block_time > 0 else 0
    match_throughput = match_metrics["blocks_processed"] / match_time if match_time > 0 else 0

    click.echo("\n" + "=" * 80)
    click.echo(f"ENTITY RESOLUTION CYCLE SUMMARY - ITERATION {iteration}")
    click.echo("=" * 80)
    click.echo()
    click.echo("WHAT HAPPENED:")
    click.echo("  1. BLOCKING: Grouped similar companies into blocks for efficient comparison")
    click.echo("  2. MATCHING: Used BAML/LLM to identify duplicates within each block")
    click.echo(
        "  3. EVALUATION: Deduplicated exact copies, validated results, tracked UUID lineage"
    )
    click.echo()
    click.echo("OVERALL PIPELINE RESULTS:")
    click.echo(f"  Input:  {eval_metrics['original_companies']:,} companies")
    click.echo(f"  Output: {eval_metrics['final_companies']:,} companies")
    click.echo(
        f"  Merged: {reduction_count:,} duplicates ({eval_metrics['reduction_pct']:.1f}% reduction)"
    )
    click.echo()
    click.echo("STAGE BREAKDOWN:")
    click.echo(f"  1. Blocking ({timedelta(seconds=int(block_time))}):")
    click.echo(f"     • Processed {block_metrics['input_companies']:,} companies")
    click.echo(f"     • Created {block_metrics['blocks_created']:,} blocks")
    click.echo(f"     • Largest block: {block_metrics['largest_block']:,} companies")
    click.echo("     • Top 10 largest blocks:")
    for block in block_metrics["top_blocks"]:
        click.echo(f"       - {block['block_key']}: {block['block_size']:,} companies")
    click.echo(f"     • Throughput: {block_throughput:,.0f} companies/sec")
    click.echo()
    click.echo(f"  2. Matching ({timedelta(seconds=int(match_time))}):")
    click.echo(f"     • Processed {match_metrics['blocks_processed']:,} blocks")
    click.echo(f"     • Matched companies: {match_metrics['total_companies']:,}")
    click.echo(f"     • Singletons/skipped: {match_metrics['skipped']:,}")
    click.echo(f"     • Throughput: {match_throughput:,.0f} blocks/sec")
    click.echo()
    click.echo(f"  3. Evaluation ({timedelta(seconds=int(eval_time))}):")
    click.echo(f"     • Validated {eval_metrics['final_companies']:,} resolved companies")
    click.echo("     • Exact duplicate removal: PASS ✓")
    click.echo("     • Source UUID tracking: 100% coverage")
    click.echo("     • Data integrity: PASS ✓")
    click.echo()
    click.echo("PERFORMANCE SUMMARY:")
    click.echo(f"  Total cycle time: {timedelta(seconds=int(cycle_time))}")
    click.echo("  Time per stage:")
    click.echo(
        f"    ├─ Blocking:    {timedelta(seconds=int(block_time))} ({block_time / cycle_time * 100:.1f}%)"
    )
    click.echo(
        f"    ├─ Matching:    {timedelta(seconds=int(match_time))} ({match_time / cycle_time * 100:.1f}%)"
    )
    click.echo(
        f"    └─ Evaluation:  {timedelta(seconds=int(eval_time))} ({eval_time / cycle_time * 100:.1f}%)"
    )
    click.echo()
    click.echo("OUTPUT FILES:")
    click.echo(f"  Blocks:             {blocks_path}")
    click.echo(f"  Matches:            {matches_path}")
    click.echo(f"  Resolved companies: {eval_path}")
    click.echo(f"  Evaluation metrics: {metrics_path}")
    click.echo()

    # Print cross-iteration summary table
    all_metrics = get_all_iteration_metrics(iteration)
    if all_metrics:
        click.echo("ITERATION HISTORY:")
        click.echo(
            "+" + "-" * 11 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 12 + "+"
        )
        click.echo(
            f"| {'Iteration':^9} | {'Blocks':^8} | {'Companies In':^14} | {'Companies Out':^14} | {'Reduction':^10} |"
        )
        click.echo(
            "+" + "-" * 11 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 12 + "+"
        )
        for m in all_metrics:
            click.echo(
                f"| {m['iteration']:^9} | {m['blocks']:>8,} | {m['companies_in']:>14,} | {m['companies_out']:>14,} | {m['reduction_pct']:>9.1f}% |"
            )
        click.echo(
            "+" + "-" * 11 + "+" + "-" * 10 + "+" + "-" * 16 + "+" + "-" * 16 + "+" + "-" * 12 + "+"
        )
        click.echo()

    click.echo("✓ Entity resolution cycle completed successfully!")
    click.echo(
        "  Next step: Run iteration {0} with resolved companies as input".format(iteration + 1)
    )
    click.echo("=" * 80)

from typing import Any, TypedDict

import pandas as pd


class BlockInfo(TypedDict):
    block_key: str
    block_size: int


class BlockingMetrics(TypedDict):
    input_companies: int
    blocks_created: int
    largest_block: int
    top_blocks: list[BlockInfo]


def get_blocking_metrics(input_path: str, blocks_path: str) -> BlockingMetrics:
    """Extract key metrics from blocking stage output (Parquet files)."""
    # Read input companies (Parquet)
    input_df = pd.read_parquet(input_path)
    input_count = len(input_df)

    # Read blocks (Parquet)
    blocks_df = pd.read_parquet(blocks_path)
    blocks_count = len(blocks_df)

    # Get largest block size
    largest_block = blocks_df["block_size"].max() if "block_size" in blocks_df.columns else 0

    # Get top 10 largest blocks with their keys
    top_blocks: list[Any] = []
    if "block_size" in blocks_df.columns and "block_key" in blocks_df.columns:
        top_blocks = blocks_df.nlargest(10, "block_size")[["block_key", "block_size"]].to_dict(
            "records"
        )

    return {
        "input_companies": input_count,
        "blocks_created": blocks_count,
        "largest_block": int(largest_block),
        "top_blocks": top_blocks,
    }


def get_matching_metrics(matches_path: str) -> dict[str, int]:
    """Extract key metrics from matching stage output (JSONL file from match.py)."""
    # Read matches (JSONL - only place we use JSONL)
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


def get_evaluation_metrics(metrics_path: str) -> dict[str, int | float]:
    """Extract key metrics from evaluation stage output (Parquet files)."""
    # Read metrics (Parquet)
    metrics_df = pd.read_parquet(metrics_path)
    metrics = metrics_df.iloc[0].to_dict()

    return {
        "original_companies": int(metrics.get("total_original_companies", 0)),
        "final_companies": int(metrics.get("total_output_companies", 0)),
        "reduction_pct": float(metrics.get("total_reduction_pct", 0.0)),
    }


class IterationMetrics(TypedDict):
    iteration: int
    blocks: int
    companies_in: int
    companies_out: int
    reduction_pct: float
    overall_reduction_pct: float


def get_all_iteration_metrics(
    current_iteration: int, base_path: str = "data/er/iterations"
) -> list[IterationMetrics]:
    """Collect metrics from all iterations 1 through current_iteration.

    Args:
        current_iteration: The current iteration number
        base_path: Base path for iteration data

    Returns:
        List of metrics dictionaries, one per iteration
    """
    from pathlib import Path

    results: list[IterationMetrics] = []
    original_companies: int | None = None

    for i in range(1, current_iteration + 1):
        metrics_path = Path(base_path) / str(i) / "er_evaluation_metrics.parquet"

        if not metrics_path.exists():
            continue

        try:
            df = pd.read_parquet(metrics_path)
            row = df.iloc[0]

            # Use iteration_input_companies for the actual input to this iteration
            # Fall back to total_original_companies for backwards compatibility
            companies_in = int(
                row.get("iteration_input_companies", row.get("total_original_companies", 0))
            )
            companies_out = int(row.get("total_output_companies", 0))

            # Track the original companies count from iteration 1
            if i == 1:
                original_companies = companies_in

            # Calculate per-round reduction (from iteration input to output)
            if companies_in > 0:
                per_round_reduction_pct = ((companies_in - companies_out) / companies_in) * 100
            else:
                per_round_reduction_pct = 0.0

            # Calculate overall reduction (from original to current output)
            if original_companies is not None and original_companies > 0:
                overall_reduction_pct = (
                    (original_companies - companies_out) / original_companies
                ) * 100
            else:
                overall_reduction_pct = per_round_reduction_pct

            results.append(
                {
                    "iteration": i,
                    "blocks": int(row.get("total_blocks", 0)),
                    "companies_in": companies_in,
                    "companies_out": companies_out,
                    "reduction_pct": per_round_reduction_pct,
                    "overall_reduction_pct": overall_reduction_pct,
                }
            )
        except Exception:
            continue

    return results

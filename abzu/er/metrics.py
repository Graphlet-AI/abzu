import pandas as pd


def get_blocking_metrics(input_path: str, blocks_path: str) -> dict[str, int]:
    """Extract key metrics from blocking stage output (Parquet files)."""
    # Read input companies (Parquet)
    input_df = pd.read_parquet(input_path)
    input_count = len(input_df)

    # Read blocks (Parquet)
    blocks_df = pd.read_parquet(blocks_path)
    blocks_count = len(blocks_df)

    # Get largest block size
    largest_block = blocks_df["block_size"].max() if "block_size" in blocks_df.columns else 0

    return {
        "input_companies": input_count,
        "blocks_created": blocks_count,
        "largest_block": int(largest_block),
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


def get_evaluation_metrics(eval_path: str, metrics_path: str) -> dict[str, int | float]:
    """Extract key metrics from evaluation stage output (Parquet files)."""
    # Read metrics (Parquet)
    metrics_df = pd.read_parquet(metrics_path)
    metrics = metrics_df.iloc[0].to_dict()

    return {
        "original_companies": int(metrics.get("total_original_companies", 0)),
        "final_companies": int(metrics.get("total_output_companies", 0)),
        "reduction_pct": float(metrics.get("total_reduction_pct", 0.0)),
    }

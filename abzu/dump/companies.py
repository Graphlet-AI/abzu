import logging

import pandas as pd

logger = logging.getLogger(__name__)


def dump_companies_main(file_path: str) -> int:
    """Dump companies from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:  # pragma: no cover - load failure path
        logger.error(f"Failed to read companies file {file_path}: {e}")
        return 1

    required_cols = {"name"}
    missing = required_cols.difference(df.columns)
    if missing:
        logger.error(f"Missing required columns: {', '.join(sorted(missing))}")
        return 1

    # Determine columns to display
    columns_to_show = ["name"]
    if "ticker" in df.columns:
        columns_to_show.append("ticker")
    if "description" in df.columns:
        columns_to_show.append("description")

    # Create header based on available columns
    if len(columns_to_show) == 1:
        header = f"{'Company':<40}"
    elif len(columns_to_show) == 2:
        header = f"{'Company':<40}{'Ticker':<10}"
    else:
        header = f"{'Company':<40}{'Ticker':<10}{'Description'}"

    print(header)

    # Sort by company name
    sorted_df = df.sort_values("name")

    for _, row in sorted_df.iterrows():
        company = row.get("name") or ""

        if len(columns_to_show) == 1:
            print(f"{company:<40}")
        elif len(columns_to_show) == 2:
            ticker_val = row.get("ticker")
            # Handle ticker as dict, string, or None
            if isinstance(ticker_val, dict):
                ticker = ticker_val.get("symbol", "")
            else:
                ticker = ticker_val or ""
            print(f"{company:<40}{ticker:<10}")
        else:
            ticker_val = row.get("ticker")
            # Handle ticker as dict, string, or None
            if isinstance(ticker_val, dict):
                ticker = ticker_val.get("symbol", "")
            else:
                ticker = ticker_val or ""
            desc = row.get("description") or ""
            print(f"{company:<40}{ticker:<10}{desc}")

    return 0

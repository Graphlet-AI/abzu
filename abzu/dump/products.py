import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def dump_products_main(file_path: str) -> int:
    """Dump company products from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:  # pragma: no cover - load failure path
        logger.error(f"Failed to read products file {file_path}: {e}")
        return 1

    required_cols = {"company_name", "name", "description"}
    missing = required_cols.difference(df.columns)
    if missing:
        logger.error(f"Missing required columns: {', '.join(sorted(missing))}")
        return 1

    header = f"{'Company':<30}{'Product':<30}{'Description'}"
    print(header)
    sorted_df = df.sort_values("company_name")
    for _, row in sorted_df.iterrows():
        company = row.get("company_name") or ""
        product = row.get("name") or ""
        desc = row.get("description") or ""
        print(f"{company:<30}{product:<30}{desc}")
    return 0

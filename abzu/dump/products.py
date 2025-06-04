import pandas as pd

from abzu.logs import get_logger

logger = get_logger(__name__)


def dump_products_main(file_path: str) -> int:
    """Dump company products from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:  # pragma: no cover - load failure path
        logger.error(f"Failed to read products file {file_path}: {e}")
        return 1

    # Handle both old and new schema
    if "company_name" not in df.columns and "manufacturer_name" in df.columns:
        df["company_name"] = df["manufacturer_name"]

    required_cols = {"name", "description"}
    missing = required_cols.difference(df.columns)
    if missing:
        logger.error(f"Missing required columns: {', '.join(sorted(missing))}")
        return 1

    header = f"{'Company':<30}{'Product':<30}{'Description'}"
    print(header)

    # Use manufacturer_name or company_name for sorting
    sort_col = "manufacturer_name" if "manufacturer_name" in df.columns else "company_name"

    if sort_col not in df.columns:
        # If neither column exists, just sort by name
        sorted_df = df.sort_values("name")
    else:
        sorted_df = df.sort_values(sort_col)

    for _, row in sorted_df.iterrows():
        # Get company name from either manufacturer_name or company_name
        company = row.get("manufacturer_name") or row.get("company_name") or ""
        product = row.get("name") or ""
        desc = row.get("description") or ""
        print(f"{company:<30}{product:<30}{desc}")
    return 0

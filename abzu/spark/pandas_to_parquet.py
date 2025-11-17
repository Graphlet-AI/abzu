"""Utility to save pandas DataFrames using PySpark for consistent parquet handling."""

from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame as SparkDataFrame
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def save_pandas_df_with_pyspark(
    df: pd.DataFrame,
    output_path: str,
    schema: StructType | None = None,
    app_name: str = "SavePandasWithPySpark",
    mode: str = "overwrite",
) -> None:
    """
    Save a pandas DataFrame to Parquet using PySpark to handle complex nested structures.

    This function ensures consistent parquet handling across the codebase by using
    PySpark's parquet writer, which properly handles nested structures like lists
    of dictionaries without requiring JSON serialization workarounds.

    Args:
        df: Pandas DataFrame to save
        output_path: Path to save the parquet file
        schema: Required PySpark schema to use
        app_name: Name for the Spark application
        mode: Write mode - "overwrite", "append", "ignore", "error"

    Example:
        >>> df = pd.DataFrame({
        ...     "id": [1, 2],
        ...     "items": [
        ...         [{"name": "a", "values": [1, 2]}, {"name": "b", "values": [3]}],
        ...         [{"name": "c", "values": [4, 5, 6]}]
        ...     ]
        ... })
        >>> save_pandas_df_with_pyspark(df, "/path/to/output.parquet")
    """
    # Get or create Spark session
    spark: SparkSession = get_spark_session(app_name)

    # IMPORTANT: Disable Arrow to preserve Python types (lists, not numpy arrays)
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

    try:
        # Handle None values in list columns - replace with empty lists
        for col in df.columns:
            if df[col].dtype == "object":
                # Check if this column contains lists
                first_non_none = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(first_non_none, list):
                    logger.debug(f"Replacing None values with empty lists in column '{col}'")
                    # Use a more careful check for None/NaN that works with all types
                    df[col] = df[col].apply(
                        lambda x: [] if x is None or (isinstance(x, float) and pd.isna(x)) else x
                    )

        logger.debug("Creating Spark DataFrame with provided schema")
        # Just try to create with schema - if it fails, it fails
        spark_df: SparkDataFrame = spark.createDataFrame(df, schema=schema)

        # Log the schema for debugging
        if logger.isEnabledFor(10):  # DEBUG level
            logger.debug("DataFrame schema:")
            spark_df.printSchema()

        # Save to parquet
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving DataFrame ({len(df)} rows) to {output_path} using PySpark")

        # Write as parquet using PySpark
        spark_df.coalesce(1).write.mode(mode).parquet(str(output_path))

        logger.info(f"Successfully saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to save DataFrame with PySpark: {e}")
        # Log column types for debugging
        for col in df.columns:
            sample = df[col].iloc[0] if len(df) > 0 else None
            logger.debug(f"Column '{col}': dtype={df[col].dtype}, sample type={type(sample)}")
        raise

    finally:
        # Note: We don't stop the spark session here as it might be reused
        # The session will be cleaned up when the process ends
        pass


def read_parquet_with_pyspark(
    input_path: str,
    app_name: str = "ReadParquetWithPySpark",
) -> pd.DataFrame:
    """
    Read a Parquet file using PySpark and convert to pandas DataFrame.

    This ensures consistent reading of parquet files, preserving Python lists
    instead of converting them to numpy arrays.

    Args:
        input_path: Path to the parquet file
        app_name: Name for the Spark application

    Returns:
        Pandas DataFrame with preserved Python types

    Example:
        >>> df = read_parquet_with_pyspark("/path/to/input.parquet")
        >>> type(df["items"].iloc[0])  # Will be list, not numpy.ndarray
        <class 'list'>
    """
    spark: SparkSession = get_spark_session(app_name)

    # IMPORTANT: Disable Arrow to preserve Python types
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

    logger.info(f"Reading parquet from {input_path} using PySpark")

    # Read parquet
    spark_df: SparkDataFrame = spark.read.parquet(input_path)

    # Convert to pandas
    df = spark_df.toPandas()

    logger.info(f"Loaded {len(df)} rows from {input_path}")

    return df

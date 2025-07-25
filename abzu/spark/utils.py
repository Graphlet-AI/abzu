#!/usr/bin/env python3
"""Utility functions for Spark operations."""
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame
from pyspark.sql.window import Window


def select_most_common_property(
    df: DataFrame,
    unique_id_column: str,
    property_column: str,
    additional_columns: Optional[list[str]] = None,
) -> DataFrame:
    """
    Select the most common value of a property for each unique identifier.

    For each unique identifier, this function:
    1. Counts occurrences of each property value
    2. Ranks property values by count (most common first)
    3. If counts are tied, selects the longest string value
    4. Returns one row per unique identifier with the selected property

    Parameters
    ----------
    df : DataFrame
        Input DataFrame containing the data
    unique_id_column : str
        Column name of the unique identifier (e.g., "name" for companies)
    property_column : str
        Column name of the property to select (e.g., "ticker")
    additional_columns : list[str], optional
        Additional columns to include in the output that are associated with
        the property (e.g., "exchange" when property is "symbol")

    Returns
    -------
    DataFrame
        DataFrame with one row per unique identifier, containing the unique_id_column,
        property_column, and any additional_columns specified

    Examples
    --------
    >>> # Select most common ticker per company
    >>> result = select_most_common_property(
    ...     companies_df,
    ...     unique_id_column="name",
    ...     property_column="ticker"
    ... )

    >>> # Select most common symbol per company with exchange info
    >>> result = select_most_common_property(
    ...     ticker_df,
    ...     unique_id_column="name",
    ...     property_column="symbol",
    ...     additional_columns=["exchange"]
    ... )
    """
    # Prepare columns to group by
    group_columns = [unique_id_column, property_column]
    if additional_columns:
        group_columns.extend(additional_columns)

    # Count occurrences of each property value per unique identifier
    counts_df = df.groupBy(*group_columns).agg(F.count("*").alias("property_count"))

    # Create window to rank by count (descending) and string length (descending) as tiebreaker
    window_spec = Window.partitionBy(unique_id_column).orderBy(
        F.desc("property_count"), F.desc(F.length(F.col(property_column)))
    )

    # Select the most common (or longest if tied) property value
    result_df = (
        counts_df.withColumn("rank", F.row_number().over(window_spec))
        .filter(F.col("rank") == 1)
        .drop("rank", "property_count")
    )

    return result_df

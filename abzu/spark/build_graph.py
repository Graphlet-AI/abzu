#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.window import Window

from abzu.config import config
from abzu.finance.symbols import suffix_mapping_expr
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def build_knowledge_graph(
    input_path: list[str] = config.get("process.kg.raw.input"),
    output_path: str = config.get("process.kg.raw.output"),
    local_mode: Optional[bool] = None,
) -> None:
    """
    Build a knowledge graph from pre-processed articles.

    Args:
        input_path: Path(s) to the input JSON files
        output_path: Path to save the output parquet files
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="build_graph",
        local_mode=local_mode,
    )

    logger.info(f"Reading processed articles from {input_path} ...")
    articles_df: DataFrame = spark.read.json(input_path)
    logger.info(f"Loaded {articles_df.count():,} processed articles")

    # Show a sample record
    articles_df.show(1, truncate=100, vertical=True)

    # Extract entities into separate dataframes
    logger.info("Extracting entities from documents ...")

    # Extract companies
    logger.info("Extracting companies ...")
    companies_raw_df = (
        articles_df.select(F.explode_outer(F.col("companies")).alias("company"))
        .filter("company IS NOT NULL")
        .select("company.*")
    )

    #
    # Get a list of company names and exchanges per symbol
    #

    tickers_df = (
        companies_raw_df.filter("ticker IS NOT NULL")
        .select("ticker.*")
        .select(F.upper("exchange").alias("exchange"), F.upper("symbol").alias("symbol"), "name")
    )
    tickers_df.show(20, truncate=100)
    logger.info(f"Total tickers: {tickers_df.count():,}")

    # Group tickers by symbol to get a list of exchanges and names
    grouped_tickers_df = tickers_df.groupby("symbol").agg(
        F.collect_list("exchange").alias("exchanges"),
        F.collect_list("name").alias("names"),
        F.count("*").alias("symbol_count"),
    )

    #
    # Tickers are sometimes attached to the symbol via a period. Take this if no exchange is provided.
    #

    # First, we need to go back to the original tickers_df to count exchange occurrences
    ticker_exchange_counts_df = (
        tickers_df.filter(F.col("exchange").isNotNull())
        .groupBy("symbol", "exchange")
        .agg(F.count("*").alias("exchange_count"))
    )

    # Use window function to rank exchanges by count for each symbol
    window_spec = Window.partitionBy("symbol").orderBy(F.desc("exchange_count"))

    most_common_exchange_df = (
        ticker_exchange_counts_df.withColumn("rank", F.row_number().over(window_spec))
        .filter(F.col("rank") == 1)
        .select("symbol", F.col("exchange").alias("most_common_exchange"))
    )

    # Join back with grouped_tickers_df
    unique_tickers_with_exchange_df = grouped_tickers_df.join(
        most_common_exchange_df, on="symbol", how="left"
    )

    # Clean up ticker symbols and extract exchange from symbol if needed
    # Handle cases like "2590.HK" where .HK indicates the exchange HKEX
    tickers_with_parsed_exchange_df = (
        unique_tickers_with_exchange_df
        # Find the last dot position (in case there are multiple dots)
        .withColumn("last_dot_pos", F.expr("INSTR(REVERSE(symbol), '.')"))
        .withColumn(
            "base_symbol",
            F.when(
                F.col("last_dot_pos") > 0,
                F.expr("SUBSTRING(symbol, 1, LENGTH(symbol) - last_dot_pos)"),
            ).otherwise(F.col("symbol")),
        )
        .withColumn(
            "symbol_suffix",
            F.when(
                F.col("last_dot_pos") > 0,
                F.expr("SUBSTRING(symbol, LENGTH(symbol) - last_dot_pos + 2, last_dot_pos)"),
            ).otherwise(None),
        )
        # Map suffix to exchange using EXCHANGE_SUFFIX_MAP
        .withColumn("mapped_exchange", suffix_mapping_expr)  # Changed this line
        # Determine final exchange with clear priority
        .withColumn(
            "final_exchange",
            F.coalesce(
                # 1. Use most common exchange from data if available
                F.col("most_common_exchange"),
                # 2. Use mapped exchange from suffix if valid
                F.col("mapped_exchange"),
                # 3. Use first exchange from list if any
                F.when(F.size("exchanges") > 0, F.col("exchanges").getItem(0)),
                # 4. Use raw suffix as last resort (for unknown suffixes)
                F.col("symbol_suffix"),
            ),
        )
        # Determine final symbol based on exchange resolution
        .withColumn(
            "final_symbol",
            F.when(
                # If we have a valid mapped exchange from suffix, use base symbol
                F.col("mapped_exchange").isNotNull(),
                F.col("base_symbol"),
            )
            .when(
                # If we have most common exchange and suffix maps to same exchange, use base symbol
                (F.col("most_common_exchange").isNotNull())
                & (F.col("most_common_exchange") == F.col("mapped_exchange")),
                F.col("base_symbol"),
            )
            .otherwise(
                # Otherwise keep original symbol (including any suffix)
                F.col("symbol")
            ),
        )
    )

    # Select final columns with optional debug information
    eval_tickers_df = tickers_with_parsed_exchange_df.select(
        F.col("final_symbol").alias("symbol"),
        F.col("final_exchange").alias("exchange"),
        "names",
        # Optional: Include debug columns to verify logic
        F.col("most_common_exchange").alias("_debug_most_common"),
        F.col("symbol_suffix").alias("_debug_suffix"),
        F.col("mapped_exchange").alias("_debug_mapped_exchange"),
    )
    eval_tickers_df.show(10, truncate=False, vertical=True)

    # Data quality check
    logger.info("Data quality summary:")
    quality_summary = eval_tickers_df.agg(
        F.count("*").alias("total_symbols"),
        F.sum(F.when(F.col("exchange").isNull(), 1).otherwise(0)).alias("missing_exchanges"),
        F.sum(F.when(F.col("exchange") == F.col("_debug_suffix"), 1).otherwise(0)).alias(
            "unmapped_suffixes"
        ),
        F.sum(F.when(F.col("_debug_mapped_exchange").isNotNull(), 1).otherwise(0)).alias(
            "symbols_with_valid_suffix"
        ),
    ).collect()[0]

    logger.info(f"Total symbols: {quality_summary['total_symbols']:,}")
    logger.info(f"Missing exchanges: {quality_summary['missing_exchanges']:,}")
    logger.info(f"Unmapped suffixes used as exchange: {quality_summary['unmapped_suffixes']:,}")
    logger.info(
        f"Symbols with valid exchange suffix: {quality_summary['symbols_with_valid_suffix']:,}"
    )

    clean_tickers_df = eval_tickers_df.select("symbol", "exchange", "names").distinct()
    clean_tickers_df

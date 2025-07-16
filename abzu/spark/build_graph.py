#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.window import Window

from abzu.config import config
from abzu.finance.symbols import EXCHANGE_SUFFIX_MAP
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

    # Handle the lack of companies in the articles gracefully
    logger.info(f"Total companies raw: {companies_raw_df.count():,}")
    if companies_raw_df.isEmpty():
        logger.warning("No companies found in the articles. Exiting.")
        return

    #
    # Get a list of company names and exchanges per symbol
    #

    tickers_df = companies_raw_df.filter("ticker IS NOT NULL").select("ticker.*")
    tickers_df.show(5, truncate=100, vertical=True)
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
        .select("symbol", F.col("exchange").alias("official_exchange"))
    )

    # Join back with unique_tickers_df
    unique_tickers_with_official_exchange_df = grouped_tickers_df.join(
        most_common_exchange_df, on="symbol", how="left"
    )

    # For symbols with only one exchange or where join didn't match, use the first exchange
    unique_tickers_with_official_exchange_df = unique_tickers_with_official_exchange_df.withColumn(
        "official_exchange",
        F.when(
            F.col("official_exchange").isNull(),
            F.when(F.size("exchanges") >= 1, F.col("exchanges").getItem(0)).otherwise(None),
        ).otherwise(F.col("official_exchange")),
    )

    # Clean up ticker symbols and extract exchange from symbol if needed
    # Handle cases like "2590.HK" where .HK indicates the exchange HKEX
    tickers_with_split_exchange_df = (
        unique_tickers_with_official_exchange_df.withColumn(
            "symbol_parts", F.split(F.col("symbol"), "\\.")
        )
        .withColumn("clean_symbol", F.col("symbol_parts").getItem(0))
        .withColumn(
            "symbol_exchange",
            F.when(F.size("symbol_parts") > 1, F.col("symbol_parts").getItem(1)).otherwise(None),
        )
        .withColumn(
            "final_exchange",
            F.when(
                # If we already have an official exchange, use it
                F.col("official_exchange").isNotNull(),
                F.col("official_exchange"),
            ).otherwise(
                # Otherwise, use the exchange from the symbol suffix
                F.col("symbol_exchange")
            ),
        )
        .withColumn(
            "final_symbol",
            F.when(
                # If official exchange exists, remove the suffix from symbol
                F.col("official_exchange").isNotNull(),
                F.col("clean_symbol"),
            ).otherwise(
                # Otherwise, keep the original symbol
                F.col("symbol")
            ),
        )
    )

    # Now nominate the clean symbol and exchange
    clean_tickers_df = tickers_with_split_exchange_df.selectExpr(
        "final_symbol AS symbol",
        "final_exchange AS exchange",
        "names",
    )
    clean_tickers_df.show(5, truncate=100, vertical=True)


EXCHANGE_SUFFIX_MAP

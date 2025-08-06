#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
from typing import Optional

import pyspark.sql.functions as F
import pyspark.sql.types as T
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

    # Extract companies and assign a random UUID id
    logger.info("Extracting companies ...")
    companies_raw_df = (
        articles_df.select(F.explode_outer(F.col("companies")).alias("company"))
        .filter("company IS NOT NULL")
        .select("company.*")
        .withColumn("id", F.expr("uuid()"))
    )

    # Store the original records with their UUIDs - they can be matched at the field level to nested
    # companies from the same post, such as Product.manufacturer or Technology.developer
    companies_raw_df.repartition(1).write.mode("overwrite").parquet(
        f"{output_path}/companies_raw.parquet"
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

    suffix_mapping_expr = F.expr(
        "CASE "
        + " ".join(
            [
                f"WHEN UPPER(symbol_suffix) = '{k}' THEN '{v}'"
                for k, v in EXCHANGE_SUFFIX_MAP.items()
            ]
        )
        + " ELSE NULL END"
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

    #
    # Now take the most common ticker per company name as the canonical ticker
    #
    companies_unique_df = companies_raw_df.select("name").distinct()

    # Explode names to join with companies
    clean_tickers_exploded_df = clean_tickers_df.select(
        "symbol", "exchange", F.explode_outer("names").alias("name")
    )

    # Count occurrences of each ticker per company name to find most common
    ticker_counts_df = clean_tickers_exploded_df.groupBy("name", "symbol", "exchange").agg(
        F.count("*").alias("ticker_count")
    )

    # Use window function to rank tickers by count for each company name
    name_window = Window.partitionBy("name").orderBy(F.desc("ticker_count"))

    most_common_ticker_df = (
        ticker_counts_df.withColumn("rank", F.row_number().over(name_window))
        .filter(F.col("rank") == 1)
        .select("name", "symbol", "exchange")
    )

    #
    # Now join tickers back to unique companies to get companies with tickers :)
    #
    companies_tickers_df = companies_unique_df.join(
        most_common_ticker_df, on="name", how="left_outer"
    ).select(
        "name",
        # Note: we drop the ticker.name field here to avoid confusion
        F.when(F.col("symbol").isNotNull(), F.struct(F.col("exchange"), F.col("symbol"))).alias(
            "ticker"
        ),
    )

    #
    # Now group companies by _ticker_ and assign them all the most common or longest company name
    #

    # First group the tickers by company name, count them and select the most common ticker per group
    companies_tickers_counts_df = (
        companies_tickers_df.filter(F.col("ticker").isNotNull())
        .groupBy("ticker", "name")
        .agg(F.count("*").alias("company_count"))
    )

    # Now choose the most common name for each ticker, or the longest name if there is a tie
    companies_name_counts_df = companies_tickers_counts_df.groupBy("ticker").agg(
        F.collect_list(F.struct("name", "company_count")).alias("name_counts"),
        F.max("company_count").alias("max_count"),
    )

    # Define a UDF to select the most common name or longest name in case of ties
    @F.udf(T.StringType())
    def select_best_name_udf(name_counts):
        # Sort by count descending, then by length descending
        sorted_names = sorted(name_counts, key=lambda x: (-x.company_count, -len(x.name)))
        if sorted_names:
            return sorted_names[0].name
        return None

    companies_tickers_names_df = (
        companies_name_counts_df.withColumn("best_name", select_best_name_udf("name_counts"))
        .filter(F.col("max_count") > 1)
        .select("ticker", "best_name")
    )

    # Now join the companies_tickers_names_df back to the companies_tickers_df
    companies_tickers_df = companies_tickers_df.join(
        companies_tickers_names_df, on="ticker", how="left_outer"
    )

    # Select final columns - may have reduced a few company names
    final_companies_tickers_df = companies_tickers_df.select(
        "name",
        F.coalesce("best_name", "name").alias("updated_name"),
        F.col("ticker").alias("updated_ticker"),
    ).distinct()

    #
    # Now combine the new company tickers back with the original companies
    #

    final_companies_df = (
        companies_raw_df.join(
            final_companies_tickers_df,
            on="name",
            how="left_outer",
        )
        .withColumn("name", F.coalesce("updated_name", "name"))
        .drop("updated_name")
    )

    # Transform the tickers without names back to the original by adding the name
    final_companies_df = (
        final_companies_df.withColumn(
            "updated_ticker",
            F.when(
                F.col("updated_ticker").isNotNull(),
                F.struct(
                    F.col("ticker.exchange"),
                    F.col("name").alias("name"),
                    F.col("ticker.symbol"),
                ),
            ).otherwise(None),
        )
        .withColumn("ticker", F.coalesce("updated_ticker", "ticker"))
        .drop("updated_ticker")
    )

    # Put 'id' colum first
    final_companies_df = final_companies_df.select(
        "id", *final_companies_df.columns[:-1]
    ).distinct()

    # Write them to a file to use in Eridu project...
    companies_output_path = f"{output_path}/companies_tickers.parquet"
    final_companies_df.repartition(1).write.mode("overwrite").parquet(
        companies_output_path,
    )
    logger.info(
        f"Saved {final_companies_tickers_df.count():,} companies to {companies_output_path}"
    )

    #
    # Now ETL Products - these are the products mentioned in the articles, manufactured by a Company
    #
    logger.info("Extracting products ...")
    products_raw_df = (
        articles_df.select(F.explode_outer(F.col("products")).alias("product"))
        .filter("product IS NOT NULL")
        .select("product.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    products_df = products_raw_df.select("id", *products_raw_df.columns[:-1])
    products_df.show(5, truncate=100, vertical=True)

    products_output_path = f"{output_path}/products.parquet"
    products_df.repartition(1).write.mode("overwrite").parquet(
        products_output_path,
    )
    logger.info(f"Saved {products_df.count():,} products to {products_output_path}")

    #
    # Now ETL Technologies - these are the technologies mentioned in the articles, developed by a Company
    #

    logger.info("Extracting technologies ...")
    technologies_raw_df = (
        articles_df.select(F.explode_outer(F.col("technologies")).alias("technology"))
        .filter("technology IS NOT NULL")
        .select("technology.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    technologies_df = technologies_raw_df.select("id", *technologies_raw_df.columns[:-1])
    technologies_df.show(5, truncate=100, vertical=True)

    technologies_output_path = f"{output_path}/technologies.parquet"
    technologies_df.repartition(1).write.mode("overwrite").parquet(
        technologies_output_path,
    )
    logger.info(f"Saved {technologies_df.count():,} technologies to {technologies_output_path}")

    #
    # Now ETL deals - these are the deals mentioned in the articles, involving two Companies
    #

    deals_raw_df = (
        articles_df.select(F.explode_outer(F.col("deals")).alias("deal"))
        .filter("deal IS NOT NULL")
        .select("deal.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    deals_df = deals_raw_df.select("id", *deals_raw_df.columns[:-1])
    deals_df.show(5, truncate=100, vertical=True)

    deals_output_path = f"{output_path}/deals.parquet"
    deals_df.repartition(1).write.mode("overwrite").parquet(
        deals_output_path,
    )
    logger.info(f"Saved {deals_df.count():,} deals to {deals_output_path}")

    #
    # Now ETL Customers - these are the customers mentioned in the articles, an edge between two Company nodes
    #

    customers_raw_df = (
        articles_df.select(F.explode_outer(F.col("customers")).alias("customer"))
        .filter("customer IS NOT NULL")
        .select("customer.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    customers_df = customers_raw_df.select("id", *customers_raw_df.columns[:-1])
    customers_df.show(5, truncate=100, vertical=True)

    customers_output_path = f"{output_path}/customers.parquet"
    customers_df.repartition(1).write.mode("overwrite").parquet(
        customers_output_path,
    )
    logger.info(f"Saved {customers_df.count():,} customers to {customers_output_path}")

    #
    # Now ETL Investors - these are the investors mentioned in the articles, an edge between two Company nodes
    #

    investors_raw_df = (
        articles_df.select(F.explode_outer(F.col("investors")).alias("investor"))
        .filter("investor IS NOT NULL")
        .select("investor.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    investors_df = investors_raw_df.select("id", *investors_raw_df.columns[:-1])
    investors_df.show(5, truncate=100, vertical=True)

    investors_output_path = f"{output_path}/investors.parquet"
    investors_df.repartition(1).write.mode("overwrite").parquet(
        investors_output_path,
    )
    logger.info(f"Saved {investors_df.count():,} investors to {investors_output_path}")

    #
    # Now ETL Partnerships - these are the partnerships mentioned in the articles, an edge between two Company nodes
    #
    partnerships_raw_df = (
        articles_df.select(F.explode_outer(F.col("partnerships")).alias("partnership"))
        .filter("partnership IS NOT NULL")
        .select("partnership.*")
        .withColumn("id", F.expr("uuid()"))
    )
    # Move 'id' to the front
    partnerships_df = partnerships_raw_df.select("id", *partnerships_raw_df.columns[:-1])
    partnerships_df.show(5, truncate=100, vertical=True)

    partnerships_output_path = f"{output_path}/partnerships.parquet"
    partnerships_df.repartition(1).write.mode("overwrite").parquet(
        partnerships_output_path,
    )
    logger.info(f"Saved {partnerships_df.count():,} partnerships to {partnerships_output_path}")

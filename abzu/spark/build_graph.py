#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
import logging
from pathlib import Path
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import types as T

from abzu.config import config
from abzu.spark.config import get_spark_session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
    processed_df: DataFrame = spark.read.json(input_path)
    logger.info(f"Loaded {processed_df.count():,} processed articles")

    # Show a sample record
    processed_df.show(1, truncate=100, vertical=True)

    # Extract entities into separate dataframes
    logger.info("Extracting entities from documents ...")

    # Extract companies with deduplication
    logger.info("Extracting companies ...")
    companies_raw_df = processed_df.select(
        F.explode_outer(F.col("companies")).alias("company")
    ).filter("company IS NOT NULL")

    # Need to handle the companies schema based on what's returned
    # First select all fields from the company struct
    companies_df = companies_raw_df.select("company.*")
    companies_df = companies_df.dropDuplicates(["name"])
    logger.info(f"Extracted {companies_df.count():,} unique companies")

    # Extract products with company relationships
    logger.info("Extracting products")
    products_raw_df = processed_df.select(
        F.explode_outer(F.col("products")).alias("product")
    ).filter("product IS NOT NULL")

    # Select all fields from the product struct
    products_df = products_raw_df.select("product.*")

    # We need to handle nested structures carefully
    # For deduplication, create name columns
    products_df = products_df.withColumn("manufacturer_name", F.col("manufacturer.name"))
    products_df = products_df.dropDuplicates(["name", "manufacturer_name"])
    logger.info(f"Extracted {products_df.count():,} unique products")

    # Extract technologies with company relationships
    logger.info("Extracting technologies ...")
    technologies_raw_df = processed_df.select(
        F.explode_outer(F.col("technologies")).alias("technology")
    ).filter("technology IS NOT NULL")

    # Select all fields from the technology struct
    technologies_df = technologies_raw_df.select("technology.*")
    logger.info("Technology expanded schema:")
    technologies_df.printSchema()

    # For deduplication, create name columns
    technologies_df = technologies_df.withColumn("developer_name", F.col("developer.name"))
    technologies_df = technologies_df.dropDuplicates(["name", "developer_name"])
    logger.info(f"Extracted {technologies_df.count():,} unique technologies")

    # Extract tickers
    logger.info("Extracting tickers ...")
    tickers_raw_df = processed_df.select(F.explode_outer(F.col("tickers")).alias("ticker")).filter(
        "ticker IS NOT NULL"
    )

    # Select all fields from the ticker struct
    ticker_field = tickers_raw_df.schema["ticker"]
    if isinstance(ticker_field.dataType, T.StructType):
        tickers_df = tickers_raw_df.select("ticker.*")
    else:
        tickers_df = tickers_raw_df.select(
            F.lit(None).cast(T.StringType()).alias("name"),
            F.col("ticker").cast(T.StringType()).alias("symbol"),
            F.lit(None).cast(T.StringType()).alias("exchange"),
        )
    tickers_df = tickers_df.dropDuplicates(["symbol"])
    logger.info(f"Extracted {tickers_df.count():,} unique ticker symbols")

    # Create company relationships
    logger.info("Creating company-ticker relationships ...")
    company_ticker_schema = companies_df.schema["ticker"]
    if isinstance(company_ticker_schema.dataType, T.StructType):
        company_ticker_df = (
            companies_df.filter(F.col("ticker").isNotNull())
            .select(
                F.col("name").alias("company_name"),
                F.col("ticker.symbol").alias("ticker_symbol"),
            )
            .dropDuplicates()
        )
    else:
        company_ticker_df = (
            companies_df.filter(F.col("ticker").isNotNull())
            .select(
                F.col("name").alias("company_name"),
                F.col("ticker").cast(T.StringType()).alias("ticker_symbol"),
            )
            .dropDuplicates()
        )

    # Product-Company relationships
    logger.info("Creating product-company relationships ...")
    product_company_df = products_df.select(
        F.col("name").alias("product_name"),
        F.col("manufacturer_name").alias("company_name"),
    ).dropDuplicates()

    # Technology-Company relationships
    logger.info("Creating technology-company relationships ...")
    tech_company_df = technologies_df.select(
        F.col("name").alias("technology_name"),
        F.col("developer_name").alias("company_name"),
    ).dropDuplicates()

    # Save data
    logger.info(f"Saving knowledge graph to {output_path} ...")
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Save all dataframes
    logger.info("Saving documents")
    processed_df.write.mode("overwrite").parquet(f"{output_path}/documents.parquet")

    logger.info("Saving entities")
    companies_df.write.mode("overwrite").parquet(f"{output_path}/companies.parquet")
    products_df.write.mode("overwrite").parquet(f"{output_path}/products.parquet")
    technologies_df.write.mode("overwrite").parquet(f"{output_path}/technologies.parquet")
    tickers_df.write.mode("overwrite").parquet(f"{output_path}/tickers.parquet")

    logger.info("Saving relationships")
    company_ticker_df.write.mode("overwrite").parquet(
        f"{output_path}/company_ticker_relationships.parquet"
    )
    product_company_df.write.mode("overwrite").parquet(
        f"{output_path}/product_company_relationships.parquet"
    )
    tech_company_df.write.mode("overwrite").parquet(
        f"{output_path}/tech_company_relationships.parquet"
    )

    logger.info("Knowledge graph build complete")

    # Log summary stats
    logger.info("Knowledge Graph Statistics:")
    logger.info(f"- Documents: {processed_df.count():,}")
    logger.info(f"- Companies: {companies_df.count():,}")
    logger.info(f"- Products: {products_df.count():,}")
    logger.info(f"- Technologies: {technologies_df.count():,}")
    logger.info(f"- Tickers: {tickers_df.count():,}")
    logger.info(f"- Company-Ticker relationships: {company_ticker_df.count():,}")
    logger.info(f"- Product-Company relationships: {product_company_df.count():,}")
    logger.info(f"- Technology-Company relationships: {tech_company_df.count():,}")

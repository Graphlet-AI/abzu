#!/usr/bin/env python3
"""Build a knowledge graph from pre-processed articles."""
import logging
from pathlib import Path

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_knowledge_graph(
    input_path: str = "data/processed_articles.jsonl",
    output_path: str = "data/knowledge_graph",
    partitions: int = 4,
) -> None:
    """Build a knowledge graph from pre-processed articles."""
    # Create SparkSession
    spark: SparkSession = (
        SparkSession.builder.appName("build_graph")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "2g")
        .getOrCreate()
    )

    # Read pre-processed articles
    logger.info(f"Reading processed articles from {input_path} ...")
    processed_df: DataFrame = spark.read.json(input_path)
    logger.info(f"Loaded {processed_df.count():,} processed articles")

    # Show a sample record
    processed_df.show(1, truncate=100, vertical=True)

    # Process and optimize the dataframe
    logger.info("Optimizing dataframe for graph extraction ...")
    processed_df = processed_df.repartition(partitions)

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
    products_df = products_df.withColumn("company_name", F.col("company.name"))
    products_df = products_df.dropDuplicates(["name", "company_name"])
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
    tickers_df = tickers_raw_df.select("ticker.*")
    tickers_df = tickers_df.dropDuplicates(["symbol"])
    logger.info(f"Extracted {tickers_df.count():,} unique ticker symbols")

    # Create company relationships
    # Company-Ticker relationships
    logger.info("Creating company-ticker relationships ...")
    company_ticker_df = (
        companies_df.filter("ticker IS NOT NULL")
        .select(
            F.col("name").alias("company_name"),
            F.col("ticker.symbol").alias("ticker_symbol"),
        )
        .dropDuplicates()
    )

    # Product-Company relationships
    logger.info("Creating product-company relationships ...")
    product_company_df = products_df.select(
        F.col("name").alias("product_name"),
        F.col("company_name"),
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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge graph from processed articles")
    parser.add_argument(
        "--input",
        default="data/processed_articles.jsonl",
        help="Input processed articles JSONL file",
    )
    parser.add_argument(
        "--output", default="data/knowledge_graph", help="Output directory for knowledge graph"
    )
    parser.add_argument(
        "--partitions", type=int, default=4, help="Number of partitions for parallel processing"
    )

    args = parser.parse_args()
    build_knowledge_graph(args.input, args.output, args.partitions)

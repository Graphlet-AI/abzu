#!/usr/bin/env python3
"""Refine the knowledge graph by creating bidirectional relationships and a unified edge list."""

import logging
from pathlib import Path

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def refine_knowledge_graph(
    input_path: str = "data/knowledge_graph",
    output_path: str = "data/refined_knowledge_graph",
    partitions: int = 4,
) -> None:
    """
    Refine the knowledge graph by creating bidirectional relationships and a unified edge list.

    Args:
        input_path: Path to the raw knowledge graph parquet files
        output_path: Path to save the refined knowledge graph
        partitions: Number of Spark partitions to use
    """
    # Create SparkSession
    spark: SparkSession = (
        SparkSession.builder.appName("refine_knowledge_graph")
        .config("spark.sql.caseSensitive", True)
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "2g")
        .getOrCreate()
    )

    spark.sparkContext.setCheckpointDir("/tmp/graphframes-checkpoints")

    # Load entity dataframes
    logger.info(f"Loading knowledge graph entities from {input_path}...")
    company_df: DataFrame = spark.read.parquet(f"{input_path}/companies.parquet")
    product_df: DataFrame = spark.read.parquet(f"{input_path}/products.parquet")
    technology_df: DataFrame = spark.read.parquet(f"{input_path}/technologies.parquet")
    ticker_df = spark.read.parquet(f"{input_path}/tickers.parquet")

    # Load relationship dataframes
    logger.info(f"Loading knowledge graph relationships from {input_path}...")
    product_company_df: DataFrame = spark.read.parquet(
        f"{input_path}/product_company_relationships"
    )
    company_ticker_df: DataFrame = spark.read.parquet(
        f"{input_path}/company_ticker_relationships.parquet"
    )
    tech_company_df: DataFrame = spark.read.parquet(
        f"{input_path}/tech_company_relationships.parquet"
    )

    # Print entity counts
    logger.info(f"Loaded {company_df.count():,} companies")
    logger.info(f"Loaded {product_df.count():,} products")
    logger.info(f"Loaded {technology_df.count():,} technologies")
    logger.info(f"Loaded {ticker_df.count():,} tickers")

    # Print relationship counts
    logger.info(f"Loaded {product_company_df.count():,} product-company relationships")
    logger.info(f"Loaded {company_ticker_df.count():,} company-ticker relationships")
    logger.info(f"Loaded {tech_company_df.count():,} technology-company relationships")

    # Create bidirectional Company->Product edges
    logger.info("Creating bidirectional company-product relationships...")
    co_sells_product_df: DataFrame = product_company_df.selectExpr(
        "company_name AS src", "product_name AS dst", "'Sells' AS relationship"
    )
    prod_sold_by_co_df: DataFrame = product_company_df.selectExpr(
        "product_name AS src", "company_name AS dst", "'SoldBy' AS relationship"
    )

    # Create bidirectional Company->Ticker edges
    logger.info("Creating bidirectional company-ticker relationships...")
    co_listed_under_ticker_df: DataFrame = company_ticker_df.selectExpr(
        "company_name AS src", "ticker_symbol AS dst", "'ListedUnder' AS relationship"
    )
    ticker_represents_co_df: DataFrame = company_ticker_df.selectExpr(
        "ticker_symbol AS src", "company_name AS dst", "'Represents' AS relationship"
    )

    # Create bidirectional Company->Technology edges
    logger.info("Creating bidirectional company-technology relationships...")
    co_develops_tech_df: DataFrame = tech_company_df.selectExpr(
        "company_name AS src", "technology_name AS dst", "'Develops' AS relationship"
    )
    tech_developed_by_co_df: DataFrame = tech_company_df.selectExpr(
        "technology_name AS src", "company_name AS dst", "'DevelopedBy' AS relationship"
    )

    # Merge all edges into a single dataframe
    logger.info("Merging all edges into a unified edge list...")
    edge_df: DataFrame = (
        co_sells_product_df.union(prod_sold_by_co_df)
        .union(co_listed_under_ticker_df)
        .union(ticker_represents_co_df)
        .union(co_develops_tech_df)
        .union(tech_developed_by_co_df)
    )

    # Create vertices dataframe
    logger.info("Creating vertices dataframe...")
    companies_vertices: DataFrame = company_df.select(
        F.col("name").alias("id"),
        F.lit("company").alias("entity_type"),
        F.to_json(F.struct("*")).alias("properties"),
    )

    products_vertices: DataFrame = product_df.select(
        F.col("name").alias("id"),
        F.lit("product").alias("entity_type"),
        F.to_json(F.struct("*")).alias("properties"),
    )

    technologies_vertices: DataFrame = technology_df.select(
        F.col("name").alias("id"),
        F.lit("technology").alias("entity_type"),
        F.to_json(F.struct("*")).alias("properties"),
    )

    tickers_vertices: DataFrame = ticker_df.select(
        F.col("symbol").alias("id"),
        F.lit("ticker").alias("entity_type"),
        F.to_json(F.struct("*")).alias("properties"),
    )

    # Union all vertices
    vertices_df: DataFrame = (
        companies_vertices.union(products_vertices)
        .union(technologies_vertices)
        .union(tickers_vertices)
        .distinct()
    )

    # Save refined knowledge graph
    logger.info(f"Saving refined knowledge graph to {output_path}...")
    Path(output_path).mkdir(parents=True, exist_ok=True)

    # Save unified edge list
    logger.info(f"Saving unified edge list ({edge_df.count():,} edges)...")
    edge_df.write.mode("overwrite").parquet(f"{output_path}/edges.parquet")

    # Save unified vertex list
    logger.info(f"Saving unified vertex list ({vertices_df.count():,} vertices)...")
    vertices_df.write.mode("overwrite").parquet(f"{output_path}/vertices.parquet")

    # Save original entities for reference
    logger.info("Saving original entities for reference...")
    company_df.write.mode("overwrite").parquet(f"{output_path}/companies.parquet")
    product_df.write.mode("overwrite").parquet(f"{output_path}/products.parquet")
    technology_df.write.mode("overwrite").parquet(f"{output_path}/technologies.parquet")
    ticker_df.write.mode("overwrite").parquet(f"{output_path}/tickers.parquet")

    # Log summary
    logger.info("Knowledge graph refinement complete!")
    logger.info(f"- Total entities: {vertices_df.count():,}")
    logger.info(f"- Total relationships: {edge_df.count():,}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Refine knowledge graph with bidirectional relationships"
    )
    parser.add_argument(
        "--input",
        default="data/knowledge_graph",
        help="Input directory with raw knowledge graph parquet files",
    )
    parser.add_argument(
        "--output",
        default="data/refined_knowledge_graph",
        help="Output directory for refined knowledge graph",
    )
    parser.add_argument(
        "--partitions",
        type=int,
        default=4,
        help="Number of partitions for parallel processing",
    )

    args = parser.parse_args()
    refine_knowledge_graph(args.input, args.output, args.partitions)

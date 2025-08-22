#!/usr/bin/env python3
"""Entity resolution blocking strategies for company matching."""
from typing import Optional

import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql import DataFrame, SparkSession

from abzu.config import config
from abzu.er.acronyms import get_acronyms
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


@F.udf(T.StringType())
def get_first_word(name: str) -> str | None:
    """Extract first word if it's at least 1 character."""
    if not name or len(name.strip()) == 0:
        return None

    words = name.strip().split()
    if words and len(words[0]) >= 1:
        return words[0].upper()
    return None


@F.udf(T.StringType())
def get_acronym(name: str) -> str | None:
    """Generate acronyms from company names."""
    if not name:
        return None
    return get_acronyms(name)


def analyze_blocking_strategies(
    companies_path: str = "data/knowledge_graph/companies.parquet",
    local_mode: Optional[bool] = None,
) -> None:
    """
    Analyze company blocking strategies by computing size distributions.

    Args:
        companies_path: Path to the companies parquet file
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="er_blocking_analysis",
        local_mode=local_mode,
    )

    logger.info(f"Loading companies from {companies_path}")
    companies_df: DataFrame = spark.read.parquet(companies_path)

    total_companies = companies_df.count()
    logger.info(f"Loaded {total_companies:,} companies")

    # Show sample of the data
    logger.info("Sample companies:")
    companies_df.show(5, truncate=False)

    # Apply blocking strategies
    logger.info("Computing blocking keys...")
    companies_with_block_keys_df = companies_df.select(
        "uuid",
        "name",
        get_first_word(F.col("name")).alias("first_word_block"),
        get_acronym(F.col("name")).alias("acronym_block"),
    )

    # Cache for multiple operations
    companies_with_block_keys_df = companies_with_block_keys_df.cache()

    # Show sample with blocking keys
    logger.info("Sample companies with blocking keys:")
    companies_with_block_keys_df.show(10, truncate=False)

    # Compute first word blocking distribution
    logger.info("Computing first word blocking distribution...")
    first_word_dist_df = (
        companies_with_block_keys_df.filter(F.col("first_word_block").isNotNull())
        .groupBy("first_word_block")
        .agg(F.count("*").alias("block_size"))
        .orderBy(F.desc("block_size"))
    )

    first_word_blocks = first_word_dist_df.count()
    first_word_companies = companies_with_block_keys_df.filter(
        F.col("first_word_block").isNotNull()
    ).count()

    logger.info(
        f"First word blocking: {first_word_blocks:,} blocks covering {first_word_companies:,} companies"
    )
    logger.info("Top 20 first word blocks:")
    first_word_dist_df.show(20, truncate=False)

    # Create histogram bins for first word block sizes
    logger.info("First word block size distribution histogram:")
    first_word_histogram_df = (
        first_word_dist_df.select(
            F.when(F.col("block_size") == 1, "1")
            .when(F.col("block_size") <= 5, "2-5")
            .when(F.col("block_size") <= 10, "6-10")
            .when(F.col("block_size") <= 20, "11-20")
            .when(F.col("block_size") <= 50, "21-50")
            .when(F.col("block_size") <= 100, "51-100")
            .otherwise("100+")
            .alias("block_size_range"),
            F.col("block_size"),
        )
        .groupBy("block_size_range")
        .agg(
            F.count("*").alias("num_blocks"), F.sum("block_size").alias("total_companies_in_range")
        )
        .orderBy(
            F.when(F.col("block_size_range") == "1", 1)
            .when(F.col("block_size_range") == "2-5", 2)
            .when(F.col("block_size_range") == "6-10", 3)
            .when(F.col("block_size_range") == "11-20", 4)
            .when(F.col("block_size_range") == "21-50", 5)
            .when(F.col("block_size_range") == "51-100", 6)
            .otherwise(7)
        )
    )
    first_word_histogram_df.show(truncate=False)

    # Compute acronym blocking distribution
    logger.info("Computing acronym blocking distribution...")
    acronym_dist_df = (
        companies_with_block_keys_df.filter(F.col("acronym_block").isNotNull())
        .groupBy("acronym_block")
        .agg(F.count("*").alias("block_size"))
        .orderBy(F.desc("block_size"))
    )

    acronym_blocks = acronym_dist_df.count()
    acronym_companies = companies_with_block_keys_df.filter(
        F.col("acronym_block").isNotNull()
    ).count()

    logger.info(
        f"Acronym blocking: {acronym_blocks:,} blocks covering {acronym_companies:,} companies"
    )
    logger.info("Top 20 acronym blocks:")
    acronym_dist_df.show(20, truncate=False)

    # Create histogram bins for acronym block sizes
    logger.info("Acronym block size distribution histogram:")
    acronym_histogram_df = (
        acronym_dist_df.select(
            F.when(F.col("block_size") == 1, "1")
            .when(F.col("block_size") <= 5, "2-5")
            .when(F.col("block_size") <= 10, "6-10")
            .when(F.col("block_size") <= 20, "11-20")
            .when(F.col("block_size") <= 50, "21-50")
            .when(F.col("block_size") <= 100, "51-100")
            .otherwise("100+")
            .alias("block_size_range"),
            F.col("block_size"),
        )
        .groupBy("block_size_range")
        .agg(
            F.count("*").alias("num_blocks"), F.sum("block_size").alias("total_companies_in_range")
        )
        .orderBy(
            F.when(F.col("block_size_range") == "1", 1)
            .when(F.col("block_size_range") == "2-5", 2)
            .when(F.col("block_size_range") == "6-10", 3)
            .when(F.col("block_size_range") == "11-20", 4)
            .when(F.col("block_size_range") == "21-50", 5)
            .when(F.col("block_size_range") == "51-100", 6)
            .otherwise(7)
        )
    )
    acronym_histogram_df.show(truncate=False)

    # Print summary statistics
    logger.info("\n" + "=" * 60)
    logger.info("BLOCKING STRATEGY SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total companies: {total_companies:,}")
    logger.info("")
    logger.info("First Word Blocking:")
    logger.info(f"  - Blocks created: {first_word_blocks:,}")
    logger.info(
        f"  - Companies covered: {first_word_companies:,} ({first_word_companies / total_companies * 100:.1f}%)"
    )
    logger.info("")
    logger.info("Acronym Blocking:")
    logger.info(f"  - Blocks created: {acronym_blocks:,}")
    logger.info(
        f"  - Companies covered: {acronym_companies:,} ({acronym_companies / total_companies * 100:.1f}%)"
    )
    logger.info("=" * 60)

    # Clean up
    companies_with_block_keys_df.unpersist()
    spark.stop()


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
    # TODO: Implement knowledge graph building logic
    _ = spark  # Placeholder to mark spark as used


if __name__ == "__main__":
    analyze_blocking_strategies()

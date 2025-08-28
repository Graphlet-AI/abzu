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


def build_blocks(
    companies_path: str = f"{config.get('process.kg.er.input')}/companies.parquet",
    output_path: str = config.get("process.kg.er.output"),
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
        app_name="build_er_blocks",
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

    # Filter out 1-size blocks for actual entity resolution
    logger.info("Filtering blocks with size > 1 for entity resolution...")

    # Get first word blocks with size > 1
    first_word_multi_blocks = first_word_dist_df.filter(F.col("block_size") > 1).select(
        "first_word_block"
    )

    # Get acronym blocks with size > 1
    acronym_multi_blocks = acronym_dist_df.filter(F.col("block_size") > 1).select("acronym_block")

    # Filter companies to only include those in multi-company blocks
    first_word_companies_filtered = companies_with_block_keys_df.join(
        first_word_multi_blocks,
        "first_word_block",
        "inner",
    ).select(
        "uuid",
        F.col("first_word_block").alias("block_key"),
        F.lit("first_word").alias("block_key_type"),
    )

    acronym_companies_filtered = companies_with_block_keys_df.join(
        acronym_multi_blocks,
        "acronym_block",
        "inner",
    ).select(
        "uuid",
        F.col("acronym_block").alias("block_key"),
        F.lit("acronym").alias("block_key_type"),
    )

    first_word_filtered_count = first_word_companies_filtered.count()
    acronym_filtered_count = acronym_companies_filtered.count()

    logger.info(f"First word blocks after filtering: {first_word_filtered_count:,} companies")
    logger.info(f"Acronym blocks after filtering: {acronym_filtered_count:,} companies")

    # Get complete company records and group by blocking keys
    logger.info("Grouping complete company records by blocking keys...")

    # Join filtered companies back with full company data
    full_companies_df = spark.read.parquet(companies_path)

    # Identify overlapping block_keys between first_word and acronym strategies
    logger.info("Identifying overlapping block_keys for merging...")

    # Union first_word and acronym companies
    all_companies_with_blocks = first_word_companies_filtered.union(acronym_companies_filtered)

    # Find overlapping block_keys by counting distinct block_key_types per block_key
    overlapping_keys = (
        all_companies_with_blocks.groupBy("block_key")
        .agg(F.countDistinct("block_key_type").alias("strategy_count"))
        .filter(F.col("strategy_count") > 1)
        .select("block_key")
    )

    overlapping_count = overlapping_keys.count()
    logger.info(f"Found {overlapping_count:,} overlapping block_keys between strategies")

    # Create combined blocks for overlapping keys
    combined_blocks = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "inner"
        )  # Only overlapping keys
        .dropDuplicates(["block_key", "uuid"])  # Remove duplicate UUIDs within each block
        .join(full_companies_df, "uuid", "inner")
        .groupBy("block_key")
        .agg(
            F.collect_list(F.struct("*")).alias("companies"),
            F.countDistinct("uuid").alias("total_companies"),
        )
        .withColumn("block_key_type", F.lit("combined"))
        .select("block_key", "block_key_type", "companies", "total_companies")
    )

    # Show top 20 overlapping block_keys by company count
    logger.info("Top 20 overlapping block_keys by company count:")
    combined_blocks.select("block_key", "total_companies").orderBy(F.desc("total_companies")).show(
        20, truncate=False
    )

    # Create separate blocks for non-overlapping keys
    first_word_only_blocks = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "left_anti"
        )  # Exclude overlapping keys
        .filter(F.col("block_key_type") == "first_word")
        .dropDuplicates(["block_key", "uuid"])  # Remove any duplicate UUIDs
        .join(full_companies_df, "uuid", "inner")
        .groupBy("block_key", "block_key_type")
        .agg(
            F.collect_list(F.struct("*")).alias("companies"),
            F.countDistinct("uuid").alias("total_companies"),
        )
    )

    acronym_only_blocks = (
        all_companies_with_blocks.join(
            overlapping_keys, "block_key", "left_anti"
        )  # Exclude overlapping keys
        .filter(F.col("block_key_type") == "acronym")
        .dropDuplicates(["block_key", "uuid"])  # Remove any duplicate UUIDs
        .join(full_companies_df, "uuid", "inner")
        .groupBy("block_key", "block_key_type")
        .agg(
            F.collect_list(F.struct("*")).alias("companies"),
            F.countDistinct("uuid").alias("total_companies"),
        )
    )

    # Combine all the blocks and sort by smallest first as those are easy
    # Filter out any blocks that ended up with only 1 company after processing
    all_blocks = (
        combined_blocks.select("block_key", "block_key_type", "companies", "total_companies")
        .union(
            first_word_only_blocks.select(
                "block_key", "block_key_type", "companies", "total_companies"
            )
        )
        .union(
            acronym_only_blocks.select(
                "block_key", "block_key_type", "companies", "total_companies"
            )
        )
        .filter(F.col("total_companies") > 1)  # Ensure we only keep blocks with 2+ companies
        .orderBy("total_companies")
    )

    # Write all the blocks together in one place
    logger.info(f"Persisting blocking groups to {output_path}/all_blocks.json")
    all_blocks.repartition(1).write.mode("overwrite").json(f"{output_path}/all_blocks.json")
    all_blocks.repartition(1).write.mode("overwrite").parquet(f"{output_path}/all_blocks.parquet")

    # Count blocks by type
    combined_block_count = combined_blocks.count()
    first_word_only_count = first_word_only_blocks.count()
    acronym_only_count = acronym_only_blocks.count()
    total_blocks = all_blocks.count()

    # Count companies in each block type
    combined_companies_count = combined_blocks.agg(F.sum("total_companies")).collect()[0][0]
    first_word_only_companies_count = first_word_only_blocks.agg(
        F.sum("total_companies")
    ).collect()[0][0]
    acronym_only_companies_count = acronym_only_blocks.agg(F.sum("total_companies")).collect()[0][0]

    logger.info("=" * 60)
    logger.info("ENTITY RESOLUTION BLOCKS CREATED")
    logger.info("=" * 60)
    logger.info(
        f"Combined Blocks (overlapping keys): {combined_block_count:,} blocks with {combined_companies_count:,} companies"
    )
    logger.info(
        f"First Word Only Blocks: {first_word_only_count:,} blocks with {first_word_only_companies_count:,} companies"
    )
    logger.info(
        f"Acronym Only Blocks: {acronym_only_count:,} blocks with {acronym_only_companies_count:,} companies"
    )
    logger.info(f"Total Blocks: {total_blocks:,} blocks")
    logger.info("=" * 60)

    # Clean up
    companies_with_block_keys_df.unpersist()
    spark.stop()


if __name__ == "__main__":
    build_blocks()

#!/usr/bin/env python3
"""Entity resolution blocking strategies for company matching."""
import os
from typing import Any, Optional

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
    companies_path: str = os.path.join(
        config.get("process.kg.er.paths.input"), "companies.parquet"
    ),
    output_path: str = config.get("process.kg.er.paths.output"),
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
        .agg(F.count("*").alias("num_blocks"), F.sum("block_size").alias("companies_in_range"))
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
        .agg(F.count("*").alias("num_blocks"), F.sum("block_size").alias("companies_in_range"))
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
            F.countDistinct("uuid").alias("block_size"),
        )
        .withColumn("block_key_type", F.lit("combined"))
        .select("block_key", "block_key_type", "companies", "block_size")
    )

    # Show top 20 overlapping block_keys by company count
    logger.info("Top 20 overlapping block_keys by company count:")
    combined_blocks.select("block_key", "block_size").orderBy(F.desc("block_size")).show(
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
            F.countDistinct("uuid").alias("block_size"),
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
            F.countDistinct("uuid").alias("block_size"),
        )
    )

    # Filter blocks before saving
    combined_blocks_filtered = combined_blocks.filter(F.col("block_size") > 1)
    first_word_blocks_filtered = first_word_only_blocks.filter(F.col("block_size") > 1)
    acronym_blocks_filtered = acronym_only_blocks.filter(F.col("block_size") > 1)

    acronym_blocks_filtered.printSchema()

    # Split large blocks (> 150 companies) into smaller chunks
    logger.info("Splitting large blocks (> 150 companies) into smaller chunks...")

    # 1) Define the class
    class _SplitLargeBlocks:
        def eval(self, block_key: str, block_key_type: str, companies: list, block_size: int):
            max_size = 150
            if block_size <= max_size:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), max_size):
                    chunk_companies = companies[i : i + max_size]
                    chunk_key = f"{block_key}_chunk_{chunk_num}"
                    yield (chunk_key, block_key_type, chunk_companies, len(chunk_companies))
                    chunk_num += 1

    # 2) Build the UDTF object (give it a new name)
    SplitLargeBlocks: Any = F.udtf(
        returnType=(
            "block_key: string, block_key_type: string, "
            "companies: array<struct<uuid:string,block_key:string,block_key_type:string,"
            "url:string,name:string,description:string,ceo:string,employees:long,"
            "founded_year:long,headquarters_location:string,id:long,linkedin_url:string,"
            "revenue_usd:long,source_ids:array<long>,source_uuids:array<string>,"
            "ticker:struct<exchange:string,id:long,name:string,symbol:string,uuid:string>,"
            "website_url:string>>, "
            "block_size: long"
        )
    )(_SplitLargeBlocks)

    # 3) Call it with columns from the SAME DF and alias all outputs
    combined_blocks_final = (
        combined_blocks_filtered.select(
            SplitLargeBlocks(
                F.col("block_key"), F.col("block_key_type"), F.col("companies"), F.col("block_size")
            ).alias("block_key", "block_key_type", "companies", "block_size")
        )
        .orderBy(F.col("block_size"))
        .cache()
    )
    first_word_blocks_final = (
        first_word_blocks_filtered.select(
            SplitLargeBlocks(
                F.col("block_key"), F.col("block_key_type"), F.col("companies"), F.col("block_size")
            ).alias("block_key", "block_key_type", "companies", "block_size")
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    acronym_blocks_final = (
        acronym_blocks_filtered.select(
            SplitLargeBlocks(
                F.col("block_key"), F.col("block_key_type"), F.col("companies"), F.col("block_size")
            ).alias("block_key", "block_key_type", "companies", "block_size")
        )
        .orderBy(F.col("block_size"))
        .cache()
    )

    # Save combined blocks separately
    combined_blocks_json_path = os.path.join(output_path, "combined_blocks.json")
    combined_blocks_parquet_path = os.path.join(output_path, "combined_blocks.parquet")
    logger.info(
        f"Persisting combined blocks to {combined_blocks_json_path} and {combined_blocks_parquet_path}"
    )
    combined_blocks_final.repartition(1).write.mode("overwrite").json(combined_blocks_json_path)
    combined_blocks_final.repartition(1).write.mode("overwrite").parquet(
        combined_blocks_parquet_path
    )

    # Save first_word_only blocks separately
    first_word_json_path = os.path.join(output_path, "first_word_blocks.json")
    first_word_parquet_path = os.path.join(output_path, "first_word_blocks.parquet")
    logger.info(
        f"Persisting first word blocks to {first_word_json_path} and {first_word_parquet_path}"
    )
    first_word_blocks_final.repartition(1).write.mode("overwrite").json(first_word_json_path)
    first_word_blocks_final.repartition(1).write.mode("overwrite").parquet(first_word_parquet_path)

    # Save acronym_only blocks separately
    acronym_json_path = os.path.join(output_path, "acronym_blocks.json")
    acronym_parquet_path = os.path.join(output_path, "acronym_blocks.parquet")
    logger.info(f"Persisting acronym blocks to {acronym_json_path} and {acronym_parquet_path}")
    acronym_blocks_final.repartition(1).write.mode("overwrite").json(acronym_json_path)
    acronym_blocks_final.repartition(1).write.mode("overwrite").parquet(acronym_parquet_path)

    # Count blocks by type (after filtering and splitting)
    combined_block_count = combined_blocks_final.count()
    first_word_only_count = first_word_blocks_final.count()
    acronym_only_count = acronym_blocks_final.count()
    total_blocks = combined_block_count + first_word_only_count + acronym_only_count

    # Debug: Show schema and sample data for verification
    logger.info("Combined blocks final schema:")
    combined_blocks_final.printSchema()
    logger.info("Sample combined blocks:")
    combined_blocks_final.select("block_key", "block_size").show(5)

    # Count companies in each block type (after filtering and splitting)
    # Use coalesce to handle nulls properly
    combined_sum_result = combined_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    combined_companies_count = combined_sum_result[0]["total"]

    first_word_sum_result = first_word_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    first_word_only_companies_count = first_word_sum_result[0]["total"]

    acronym_sum_result = acronym_blocks_final.agg(
        F.coalesce(F.sum("block_size"), F.lit(0)).alias("total")
    ).collect()
    acronym_only_companies_count = acronym_sum_result[0]["total"]

    # Get original counts before splitting for comparison
    original_combined_count = combined_blocks_filtered.count()
    original_first_word_count = first_word_blocks_filtered.count()
    original_acronym_count = acronym_blocks_filtered.count()

    logger.info("=" * 60)
    logger.info("ENTITY RESOLUTION BLOCKS CREATED")
    logger.info("=" * 60)
    logger.info(
        f"Combined Blocks (overlapping keys): {combined_block_count:,} blocks with {combined_companies_count:,} companies"
    )
    if combined_block_count != original_combined_count:
        logger.info(f"  (Split from {original_combined_count:,} original blocks)")
    logger.info(f"  Saved to: {combined_blocks_json_path} and {combined_blocks_parquet_path}")
    logger.info(
        f"First Word Only Blocks: {first_word_only_count:,} blocks with {first_word_only_companies_count:,} companies"
    )
    if first_word_only_count != original_first_word_count:
        logger.info(f"  (Split from {original_first_word_count:,} original blocks)")
    logger.info(f"  Saved to: {first_word_json_path} and {first_word_parquet_path}")
    logger.info(
        f"Acronym Only Blocks: {acronym_only_count:,} blocks with {acronym_only_companies_count:,} companies"
    )
    if acronym_only_count != original_acronym_count:
        logger.info(f"  (Split from {original_acronym_count:,} original blocks)")
    logger.info(f"  Saved to: {acronym_json_path} and {acronym_parquet_path}")
    logger.info(f"Total Blocks: {total_blocks:,} blocks (all blocks ≤ 150 companies)")
    logger.info("=" * 60)

    # Clean up
    companies_with_block_keys_df.unpersist()
    spark.stop()


if __name__ == "__main__":
    build_blocks()

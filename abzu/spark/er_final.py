#!/usr/bin/env python3
"""Final cross-block deduplication using UUID blocking."""
import os
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from abzu.er.match import match_entities
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.schemas import (
    BLOCK_FIELDS,
    build_udtf_return_type,
    get_company_fields_without_blocks,
    normalize_company_dataframe,
)

logger = get_logger(__name__)


def build_uuid_blocks(
    input_path: str,
    output_path: str,
    local_mode: Optional[bool] = None,
    max_block_size: int = 50,
) -> None:
    """
    Create UUID-based blocks from resolved companies for final deduplication.

    This treats UUID as just another blocking key, following the same pattern
    as first_word and acronym blocking.

    Args:
        input_path: Path to matches.json from previous matching step
        output_path: Path to save UUID blocks
        local_mode: Whether to run in local mode
        max_block_size: Maximum companies per block before splitting
    """
    spark: SparkSession = get_spark_session(
        app_name="build_uuid_blocks",
        local_mode=local_mode,
    )

    logger.info(f"Loading resolved companies from {input_path}")
    matches_df: DataFrame = spark.read.json(input_path)

    # Explode resolved_companies from blocks
    logger.info("Exploding resolved companies from blocks...")
    companies_df_raw = matches_df.select(F.explode("resolved_companies").alias("company")).select(
        "company.*"
    )

    # Normalize schema
    logger.info("Normalizing company schema...")
    companies_df = normalize_company_dataframe(companies_df_raw, preserve_extra_fields=False)

    total_companies = companies_df.count()
    logger.info(f"Total resolved companies: {total_companies:,}")

    # Group by UUID (treating UUID as a blocking key)
    logger.info("Grouping companies by UUID...")
    uuid_groups = (
        companies_df.groupBy("uuid")
        .agg(F.count("*").alias("company_count"))
        .filter(F.col("company_count") > F.lit(1))  # type: ignore[call-arg,operator]
    )

    duplicate_uuids = uuid_groups.count()
    duplicate_companies = uuid_groups.agg(F.sum("company_count")).collect()[0][0]

    logger.info(f"Found {duplicate_uuids:,} UUIDs with duplicates")
    logger.info(f"Total duplicate company records: {duplicate_companies:,}")

    if duplicate_uuids == 0:
        logger.info("No duplicate UUIDs found - skipping UUID blocking")
        # Save empty blocks file
        empty_blocks = spark.createDataFrame(
            [], schema="block_key string, block_key_type string, companies array<struct<>>"
        )
        empty_blocks.coalesce(1).write.mode("overwrite").json(output_path)
        return

    # Get company fields
    company_fields = get_company_fields_without_blocks()

    # Create UUID blocks (same pattern as er_block.py)
    uuid_blocks_temp = (
        companies_df.join(uuid_groups.select("uuid"), "uuid", "inner")
        .select(
            F.col("uuid").alias("block_key"),
            F.lit("uuid").alias("block_key_type"),
            F.struct(*company_fields).alias("company"),
        )
        .groupBy("block_key", "block_key_type")
        .agg(F.collect_list("company").alias("companies"))
        .withColumn("company_count", F.size("companies"))
    )

    logger.info("UUID block size distribution:")
    uuid_blocks_temp.groupBy("company_count").count().orderBy("company_count").show(20)

    # Split large blocks
    logger.info(f"Splitting blocks larger than {max_block_size}...")

    # Use centralized UDTF return type from schemas.py for consistency
    # This ensures block_size field is always included (not company_count)
    udtf_return_type = build_udtf_return_type()

    @F.udtf(returnType=udtf_return_type)  # type: ignore
    class SplitLargeBlocks:
        def eval(
            self,
            block_key: str,
            block_key_type: str,
            companies: list[dict],  # type: ignore
            block_size: int,
        ):  # type: ignore
            if block_size <= max_block_size:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), max_block_size):
                    chunk_companies = companies[i : i + max_block_size]
                    chunk_key = f"{block_key}_chunk_{chunk_num}"
                    yield (chunk_key, block_key_type, chunk_companies, len(chunk_companies))
                    chunk_num += 1

    # Register the UDTF for SQL use
    spark.udtf.register("split_large_uuid_blocks", SplitLargeBlocks)  # type: ignore

    # Create temp view and apply UDTF using SQL
    uuid_blocks_temp.createOrReplaceTempView("uuid_blocks_temp")
    uuid_blocks = spark.sql(
        """
        SELECT udtf_output.* FROM uuid_blocks_temp,
        LATERAL split_large_uuid_blocks(block_key, block_key_type, companies, company_count) AS udtf_output
        """
    )

    final_block_count = uuid_blocks.count()
    logger.info(f"Final UUID blocks after splitting: {final_block_count:,}")

    # Save blocks with canonical BLOCK_FIELDS from schemas.py
    # The UDTF already returns block_size (not company_count) via build_udtf_return_type()
    logger.info(f"Saving UUID blocks to {output_path}")
    uuid_blocks.select(*BLOCK_FIELDS).coalesce(1).write.mode("overwrite").json(output_path)

    logger.info("UUID blocking complete!")


def deduplicate_resolved_companies(
    matches_path: str,
    output_path: str,
    iteration: int = 1,
    local_mode: Optional[bool] = None,
    batch_size: int = 10,
) -> dict[str, int]:
    """
    Deduplicate resolved companies across blocks using UUID blocking + matching.

    This follows the same pattern as the regular ER pipeline:
    1. Build UUID blocks (group by UUID)
    2. Match companies within UUID blocks (same as regular matching)
    3. Output final deduplicated companies

    Args:
        matches_path: Path to matches.json from previous matching step
        output_path: Path to save final deduplicated companies
        iteration: Iteration number
        local_mode: Whether to run in local mode
        batch_size: Batch size for BAML matching

    Returns:
        Dictionary with metrics (input_count, duplicate_count, output_count)
    """
    spark: SparkSession = get_spark_session(
        app_name="deduplicate_resolved_companies",
        local_mode=local_mode,
    )

    logger.info(f"Starting final deduplication for iteration {iteration}")
    logger.info(f"Input:  {matches_path}")
    logger.info(f"Output: {output_path}")

    # Step 1: Build UUID blocks
    uuid_blocks_path = output_path.replace("companies_final", "uuid_blocks")
    build_uuid_blocks(
        input_path=matches_path,
        output_path=uuid_blocks_path,
        local_mode=local_mode,
        max_block_size=50,
    )

    # Step 2: Match companies within UUID blocks (reuse existing match logic)
    logger.info("Matching companies within UUID blocks...")
    uuid_matches_path = output_path.replace("companies_final", "uuid_matches")

    match_entities(
        blocks_path=uuid_blocks_path,
        output_path=uuid_matches_path,
        iteration=iteration,
        batch_size=batch_size,
        limit=None,  # Process all
    )

    # Step 3: Combine UUID-matched companies with original resolved companies
    logger.info("Combining UUID-matched companies with original resolved companies...")

    # Read original matches
    original_matches_df = spark.read.json(matches_path)
    original_companies_df = original_matches_df.select(
        F.explode("resolved_companies").alias("company")
    ).select("company.*")

    # Normalize
    original_companies_df = normalize_company_dataframe(
        original_companies_df, preserve_extra_fields=False
    )

    input_count = original_companies_df.count()
    logger.info(f"Original resolved companies: {input_count:,}")

    # Check if we had any UUID duplicates
    if not os.path.exists(uuid_matches_path.replace(".json", "")):
        logger.info("No UUID duplicates - using original companies as final output")
        final_companies_df = original_companies_df
        duplicate_count = 0
    else:
        # Read UUID matches
        uuid_matches_df = spark.read.json(uuid_matches_path)

        # Get UUIDs that were matched (have duplicates)
        matched_uuids_df = (
            uuid_matches_df.select(F.explode("resolved_companies").alias("company"))
            .select("company.uuid")
            .distinct()
        )

        # Get UUID-deduplicated companies
        uuid_deduplicated_df = uuid_matches_df.select(
            F.explode("resolved_companies").alias("company")
        ).select("company.*")

        uuid_deduplicated_df = normalize_company_dataframe(
            uuid_deduplicated_df, preserve_extra_fields=False
        )

        # Get companies that were NOT in UUID blocks (no duplicates)
        unique_companies_df = original_companies_df.join(
            matched_uuids_df, on="uuid", how="left_anti"
        )

        # Combine: UUID-deduplicated + unique (non-duplicate) companies
        final_companies_df = uuid_deduplicated_df.union(unique_companies_df)

        duplicate_count = input_count - final_companies_df.count()

    output_count = final_companies_df.count()

    logger.info("Final deduplication complete!")
    logger.info(f"  Input:      {input_count:,} companies")
    logger.info(f"  Duplicates: {duplicate_count:,} companies merged")
    logger.info(f"  Output:     {output_count:,} companies")

    # Save final deduplicated companies
    logger.info(f"Saving final deduplicated companies to {output_path}")
    final_companies_df.coalesce(1).write.mode("overwrite").json(output_path)

    return {
        "input_count": input_count,
        "duplicate_count": duplicate_count,
        "output_count": output_count,
    }

#!/usr/bin/env python3
"""Final cross-block deduplication using UUID and name blocking."""
import os
from typing import Any, Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from abzu.config import config
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

MAX_BLOCK_SIZE = config.get("process.kg.er.max_block_size", 50)


def build_uuid_blocks(
    matches_path: str,
    output_path: str,
    local_mode: Optional[bool] = None,
    max_block_size: int = 50,
) -> None:
    """
    Create UUID-based blocks from resolved companies for final deduplication.

    This treats UUID as just another blocking key, following the same pattern
    as first_word and acronym blocking.

    Args:
        matches_path: Path to matches.jsonl from previous matching step
        output_path: Path to save UUID blocks
        local_mode: Whether to run in local mode
        max_block_size: Maximum companies per block before splitting
    """
    # Use provided max_block_size or fall back to config
    if max_block_size:
        logger.info(f"Using provided max block size of {max_block_size}")
        actual_max_block_size = max_block_size
    else:
        logger.info(f"Using default max block size of {MAX_BLOCK_SIZE}")
        actual_max_block_size = MAX_BLOCK_SIZE

    spark: SparkSession = get_spark_session(
        app_name="build_uuid_blocks",
        local_mode=local_mode,
    )

    logger.info(f"Loading resolved companies from {matches_path}")
    matches_df: DataFrame = spark.read.json(matches_path)

    # Explode resolved_companies from blocks
    logger.info("Exploding resolved companies from blocks...")
    companies_df_raw = matches_df.select(F.explode("resolved_companies").alias("company")).select(
        "company.*"
    )

    # Normalize schema
    logger.info("Normalizing company schema...")
    companies_df = normalize_company_dataframe(companies_df_raw, preserve_extra_fields=True)

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
        empty_blocks.coalesce(1).write.mode("overwrite").parquet(output_path)
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
        .withColumn("block_size", F.size("companies"))
    )

    logger.info("UUID block size distribution:")
    uuid_blocks_temp.groupBy("block_size").count().orderBy("block_size").show(20)

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
            companies: list[dict[str, Any]],
            block_size: int,
        ):  # type: ignore
            if block_size <= actual_max_block_size:
                yield (block_key, block_key_type, companies, block_size)
            else:
                chunk_num = 1
                for i in range(0, len(companies), actual_max_block_size):
                    chunk_companies = companies[i : i + actual_max_block_size]
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
        LATERAL split_large_uuid_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
        """
    )

    final_block_count = uuid_blocks.count()
    logger.info(f"Final UUID blocks after splitting: {final_block_count:,}")

    # Save blocks with canonical BLOCK_FIELDS from schemas.py
    # The UDTF already returns block_size (not company_count) via build_udtf_return_type()
    logger.info(f"Saving UUID blocks to {output_path}")
    uuid_blocks.select(*BLOCK_FIELDS).coalesce(1).write.mode("overwrite").parquet(output_path)

    logger.info("UUID blocking complete!")


def build_name_blocks(
    input_path: str,
    output_path: str,
    local_mode: Optional[bool] = None,
    max_block_size: int = 50,
) -> None:
    """
    Create name-based blocks from resolved companies for final deduplication.

    This treats the complete company name as a blocking key, catching duplicates
    that have identical names but different UUIDs.

    Args:
        input_path: Path to matches.jsonl from previous matching step
        output_path: Path to save name blocks
        local_mode: Whether to run in local mode
        max_block_size: Maximum companies per block before splitting
    """
    spark: SparkSession = get_spark_session(
        app_name="build_name_blocks",
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
    companies_df = normalize_company_dataframe(companies_df_raw, preserve_extra_fields=True)

    total_companies = companies_df.count()
    logger.info(f"Total resolved companies: {total_companies:,}")

    # Group by name (treating complete name as a blocking key)
    # Normalize name: lowercase and trim whitespace
    logger.info("Grouping companies by name...")
    companies_with_normalized_name = companies_df.withColumn(
        "normalized_name", F.lower(F.trim(F.col("name")))
    )

    name_groups = (
        companies_with_normalized_name.groupBy("normalized_name")
        .agg(F.count("*").alias("company_count"))
        .filter(F.col("company_count") > F.lit(1))  # type: ignore[call-arg,operator]
    )

    duplicate_names = name_groups.count()
    duplicate_companies = name_groups.agg(F.sum("company_count")).collect()[0][0]

    logger.info(f"Found {duplicate_names:,} names with duplicates")
    logger.info(f"Total duplicate company records: {duplicate_companies:,}")

    if duplicate_names == 0:
        logger.info("No duplicate names found - skipping name blocking")
        # Save empty blocks file
        empty_blocks = spark.createDataFrame(
            [], schema="block_key string, block_key_type string, companies array<struct<>>"
        )
        empty_blocks.coalesce(1).write.mode("overwrite").parquet(output_path)
        return

    # Get company fields
    company_fields = get_company_fields_without_blocks()

    # Create name blocks (same pattern as UUID blocking)
    name_blocks_temp = (
        companies_with_normalized_name.join(
            name_groups.select("normalized_name"), "normalized_name", "inner"
        )
        .select(
            F.col("normalized_name").alias("block_key"),
            F.lit("name").alias("block_key_type"),
            F.struct(*company_fields).alias("company"),
        )
        .groupBy("block_key", "block_key_type")
        .agg(F.collect_list("company").alias("companies"))
        .withColumn("block_size", F.size("companies"))
    )

    logger.info("Name block size distribution:")
    name_blocks_temp.groupBy("block_size").count().orderBy("block_size").show(20)

    # Split large blocks
    logger.info(f"Splitting blocks larger than {max_block_size}...")

    # Use centralized UDTF return type from schemas.py for consistency
    udtf_return_type = build_udtf_return_type()

    @F.udtf(returnType=udtf_return_type)  # type: ignore
    class SplitLargeNameBlocks:
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
    spark.udtf.register("split_large_name_blocks", SplitLargeNameBlocks)  # type: ignore

    # Create temp view and apply UDTF using SQL
    name_blocks_temp.createOrReplaceTempView("name_blocks_temp")
    name_blocks = spark.sql(
        """
        SELECT udtf_output.* FROM name_blocks_temp,
        LATERAL split_large_name_blocks(block_key, block_key_type, companies, block_size) AS udtf_output
        """
    )

    final_block_count = name_blocks.count()
    logger.info(f"Final name blocks after splitting: {final_block_count:,}")

    # Save blocks with canonical BLOCK_FIELDS from schemas.py
    logger.info(f"Saving name blocks to {output_path}")
    name_blocks.select(*BLOCK_FIELDS).coalesce(1).write.mode("overwrite").parquet(output_path)

    logger.info("Name blocking complete!")


def deduplicate_resolved_companies(
    matches_path: str,
    output_path: str,
    uuid_blocks_path: str,
    uuid_matches_path: str,
    iteration: int = 1,
    local_mode: Optional[bool] = None,
    batch_size: int = 10,
) -> dict[str, int]:
    """
    Deduplicate resolved companies across blocks using UUID and name blocking.

    This follows the same pattern as the regular ER pipeline:
    1. Build UUID blocks (group by UUID) and name blocks (group by complete name)
    2. Match companies within blocks (same as regular matching)
    3. Output final deduplicated companies

    Args:
        matches_path: Path to matches.jsonl from previous matching step
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
    logger.info(f"UUID Blocks: {uuid_blocks_path}")
    logger.info(f"UUID Matches: {uuid_matches_path}")

    # Read original matches to get input count
    original_matches_df = spark.read.json(matches_path)
    original_companies_df = original_matches_df.select(
        F.explode("resolved_companies").alias("company")
    ).select("company.*")

    # Normalize
    original_companies_df = normalize_company_dataframe(
        original_companies_df, preserve_extra_fields=True
    )

    input_count = original_companies_df.count()
    logger.info(f"Original resolved companies: {input_count:,}")

    # ========== PHASE 1: UUID BLOCKING ==========
    logger.info("=== Phase 1: UUID Blocking ===")
    build_uuid_blocks(
        matches_path=matches_path,
        output_path=uuid_blocks_path,
        local_mode=local_mode,
        max_block_size=50,
    )

    # Match companies within UUID blocks
    logger.info("Matching companies within UUID blocks...")

    match_entities(
        blocks_path=uuid_blocks_path,
        output_path=uuid_matches_path,
        iteration=iteration,
        batch_size=batch_size,
        limit=None,
    )

    # Apply UUID deduplication
    uuid_has_matches = os.path.exists(uuid_matches_path)

    if uuid_has_matches:
        uuid_matches_df = spark.read.json(uuid_matches_path)

        # Get UUIDs that were in UUID blocks (from original_companies, not resolved)
        # These are the UUIDs we need to exclude from the left_anti join
        matched_uuids_df = (
            uuid_matches_df.select(F.explode("original_companies").alias("company"))
            .select("company.uuid")
            .distinct()
        )

        # Get UUID-deduplicated companies
        uuid_deduplicated_df = uuid_matches_df.select(
            F.explode("resolved_companies").alias("company")
        ).select("company.*")

        uuid_deduplicated_df = normalize_company_dataframe(
            uuid_deduplicated_df, preserve_extra_fields=True
        )

        # Get companies that were NOT in UUID blocks
        unique_companies_df = original_companies_df.join(
            matched_uuids_df, on="uuid", how="left_anti"
        )

        # Combine after UUID dedup
        # Use unionByName to match columns by name instead of position, preventing schema misalignment
        after_uuid_df = uuid_deduplicated_df.unionByName(
            unique_companies_df, allowMissingColumns=True
        )
        uuid_dedup_count = input_count - after_uuid_df.count()
        logger.info(f"UUID deduplication merged {uuid_dedup_count:,} companies")
    else:
        logger.info("No UUID duplicates found")
        after_uuid_df = original_companies_df
        uuid_dedup_count = 0

    after_uuid_count = after_uuid_df.count()
    logger.info(f"Companies after UUID dedup: {after_uuid_count:,}")

    # ========== PHASE 2: NAME BLOCKING ==========
    logger.info("=== Phase 2: Name Blocking ===")

    # Save intermediate results for name blocking
    intermediate_path = output_path.replace("companies_final", "after_uuid_dedup")
    # Create a structure that build_name_blocks expects (matches.parquet format)
    intermediate_df = (
        after_uuid_df.select(F.struct("*").alias("company"))
        .groupBy()
        .agg(F.collect_list("company").alias("resolved_companies"))
        .withColumn("block_key", F.lit("intermediate"))
        .withColumn("block_key_type", F.lit("intermediate"))
    )
    intermediate_df.coalesce(1).write.mode("overwrite").parquet(intermediate_path)

    name_blocks_path = output_path.replace("companies_final", "name_blocks")
    build_name_blocks(
        input_path=intermediate_path,
        output_path=name_blocks_path,
        local_mode=local_mode,
        max_block_size=50,
    )

    # Match companies within name blocks
    logger.info("Matching companies within name blocks...")
    name_matches_path = output_path.replace("companies_final.parquet", "name_matches.jsonl")

    match_entities(
        blocks_path=name_blocks_path,
        output_path=name_matches_path,
        iteration=iteration,
        batch_size=batch_size,
        limit=None,
    )

    # Apply name deduplication
    name_has_matches = os.path.exists(name_matches_path)

    if name_has_matches:
        name_matches_df = spark.read.json(name_matches_path)

        # Get UUIDs that were in name blocks (from original_companies, not resolved)
        # These are the UUIDs we need to exclude from the left_anti join
        name_matched_uuids_df = (
            name_matches_df.select(F.explode("original_companies").alias("company"))
            .select("company.uuid")
            .distinct()
        )

        # Get name-deduplicated companies
        name_deduplicated_df = name_matches_df.select(
            F.explode("resolved_companies").alias("company")
        ).select("company.*")

        name_deduplicated_df = normalize_company_dataframe(
            name_deduplicated_df, preserve_extra_fields=True
        )

        # Get companies that were NOT in name blocks
        unique_after_name_df = after_uuid_df.join(name_matched_uuids_df, on="uuid", how="left_anti")

        # Combine after name dedup
        # Use unionByName to match columns by name instead of position, preventing schema misalignment
        final_companies_df = name_deduplicated_df.unionByName(
            unique_after_name_df, allowMissingColumns=True
        )
        name_dedup_count = after_uuid_count - final_companies_df.count()
        logger.info(f"Name deduplication merged {name_dedup_count:,} companies")
    else:
        logger.info("No name duplicates found")
        final_companies_df = after_uuid_df
        name_dedup_count = 0

    output_count = final_companies_df.count()
    duplicate_count = input_count - output_count

    logger.info("=== Final Deduplication Complete ===")
    logger.info(f"  Input:           {input_count:,} companies")
    logger.info(f"  UUID duplicates: {uuid_dedup_count:,} companies merged")
    logger.info(f"  Name duplicates: {name_dedup_count:,} companies merged")
    logger.info(f"  Total merged:    {duplicate_count:,} companies")
    logger.info(f"  Output:          {output_count:,} companies")

    # Save final deduplicated companies
    logger.info(f"Saving final deduplicated companies to {output_path}")
    final_companies_df.coalesce(1).write.mode("overwrite").parquet(output_path)

    return {
        "input_count": input_count,
        "uuid_duplicate_count": uuid_dedup_count,
        "name_duplicate_count": name_dedup_count,
        "duplicate_count": duplicate_count,
        "output_count": output_count,
    }

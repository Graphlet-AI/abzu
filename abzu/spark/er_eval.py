#!/usr/bin/env python3
"""Entity resolution match evaluation using PySpark."""
import logging
import os
from typing import Optional

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session

logger = get_logger(__name__)


def evaluate_er_matches(
    matches_path: str = config.get("process.kg.er.paths.names.matches"),
    raw_companies_path: str = os.path.join(
        config.get("process.kg.raw.output"), "companies.parquet"
    ),
    output_path: str = config.get("process.kg.er.paths.names.eval"),
    local_mode: Optional[bool] = None,
) -> None:
    """
    Evaluate entity resolution matches by exploding companies and validating source UUIDs.

    This function:
    1. Explodes resolved companies from blocks
    2. Creates companies_resolved.json/parquet files
    3. Reports metrics on data reduction and UUID overlap
    4. Validates source_uuids against raw companies data
    5. Removes invalid source_uuids and reports error percentage

    Args:
        matches_path: Path to the matches parquet file from ER matching
        raw_companies_path: Path to the raw companies parquet file (unmerged records)
        output_path: Directory path to save evaluation results
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="evaluate_er_matches",
        local_mode=local_mode,
    )

    logger.info(f"Loading matches from {matches_path}")
    matches_df: DataFrame = spark.read.parquet(matches_path)

    logger.info(f"Loading raw companies from {raw_companies_path}")
    raw_companies_df: DataFrame = spark.read.parquet(raw_companies_path)

    total_blocks = matches_df.count()
    logger.info(f"Loaded {total_blocks:,} blocks from matches")

    # Show sample of matches data
    if logger.isEnabledFor(logging.DEBUG):
        logger.info("Sample matches data:")
        matches_df.show(3, truncate=False)

    # Explode resolved companies from blocks, keeping block metadata
    logger.info("Exploding resolved companies from blocks...")
    resolved_companies_df = matches_df.select(
        F.col("block_key").alias("match_block_key"),
        F.col("block_key_type").alias("match_block_key_type"),
        F.explode("resolved_companies").alias("company"),
    ).select("match_block_key", "match_block_key_type", "company.*")

    # Get counts for comparison - raw first, then resolved
    total_raw_companies = raw_companies_df.count()
    unique_raw_companies = raw_companies_df.select("uuid").distinct().count()
    logger.info(f"Raw companies: {total_raw_companies:,} total, {unique_raw_companies:,} unique")

    total_resolved_companies = resolved_companies_df.count()
    unique_resolved_companies = resolved_companies_df.select("uuid").distinct().count()
    logger.info(
        f"Resolved companies: {total_resolved_companies:,} total, {unique_resolved_companies:,} unique"
    )

    # Calculate data reduction metrics
    reduction_count = total_raw_companies - unique_resolved_companies
    reduction_percentage = (
        (reduction_count / total_raw_companies) * 100 if total_raw_companies > 0 else 0
    )

    logger.info(f"Data reduction: {reduction_count:,} companies ({reduction_percentage:.2f}%)")

    # Verify that resolved companies have new UUIDs (should be 0% overlap)
    raw_uuids = raw_companies_df.select("uuid").distinct()
    resolved_uuids = resolved_companies_df.select("uuid").distinct()

    overlapping_uuids = raw_uuids.intersect(resolved_uuids).count()
    overlap_percentage = (
        (overlapping_uuids / unique_raw_companies) * 100 if unique_raw_companies > 0 else 0
    )

    logger.info(
        f"New UUID verification: {overlapping_uuids:,} ({overlap_percentage:.2f}%) resolved companies reuse raw UUIDs (should be 0%)"
    )

    # Validate source_uuids - explode them first
    logger.info("Validating source UUIDs...")
    resolved_with_source_uuids = resolved_companies_df.filter(
        F.col("source_uuids").isNotNull() & (F.size("source_uuids") > 0)
    ).select(
        "uuid",
        "name",
        "match_block_key",
        "match_block_key_type",
        F.explode("source_uuids").alias("source_uuid"),
    )

    total_source_uuid_refs = resolved_with_source_uuids.count()
    logger.info(f"Total source UUID references: {total_source_uuid_refs:,}")

    # Get unique source UUIDs to compare with raw companies
    unique_source_uuids = resolved_with_source_uuids.select("source_uuid").distinct().count()
    source_coverage_percentage = (
        (unique_source_uuids / unique_raw_companies) * 100 if unique_raw_companies > 0 else 0
    )

    logger.info(
        f"Unique source UUIDs: {unique_source_uuids:,} ({source_coverage_percentage:.2f}% coverage of raw companies)"
    )

    # INNER JOIN with raw companies to find valid source_uuids
    raw_uuids_distinct = raw_companies_df.select("uuid").distinct().alias("raw")
    valid_source_uuids = resolved_with_source_uuids.join(
        raw_uuids_distinct,
        resolved_with_source_uuids.source_uuid == raw_uuids_distinct.uuid,
        how="inner",
    ).select(
        resolved_with_source_uuids.uuid.alias("resolved_uuid"),
        resolved_with_source_uuids.source_uuid,
    )

    valid_source_uuid_count = valid_source_uuids.count()
    invalid_source_uuid_count = total_source_uuid_refs - valid_source_uuid_count
    error_percentage = (
        (invalid_source_uuid_count / total_source_uuid_refs) * 100
        if total_source_uuid_refs > 0
        else 0
    )

    logger.info(f"Valid source UUIDs: {valid_source_uuid_count:,}")
    logger.info(f"Invalid source UUIDs: {invalid_source_uuid_count:,} ({error_percentage:.2f}%)")

    # Get list of valid source_uuids per resolved company
    valid_source_uuids_per_company = valid_source_uuids.groupBy("resolved_uuid").agg(
        F.collect_list("source_uuid").alias("valid_source_uuids")
    )

    # Update resolved companies with only valid source_uuids
    cleaned_resolved_companies = (
        resolved_companies_df.join(
            valid_source_uuids_per_company,
            resolved_companies_df.uuid == valid_source_uuids_per_company.resolved_uuid,
            how="left",
        )
        .drop("source_uuids")
        .drop("resolved_uuid")
        .select("*", F.coalesce("valid_source_uuids", F.array()).alias("source_uuids"))
        .drop("valid_source_uuids")
    )

    # Save companies_resolved files - both Parquet and single JSON file
    companies_resolved_parquet = os.path.join(output_path, "companies_resolved.parquet")
    companies_resolved_json = os.path.join(output_path, "companies_resolved.json")

    logger.info(f"Saving companies_resolved.parquet to {companies_resolved_parquet}")
    cleaned_resolved_companies.write.mode("overwrite").parquet(companies_resolved_parquet)

    logger.info(f"Saving companies_resolved.json to {companies_resolved_json}")
    cleaned_resolved_companies.coalesce(1).write.mode("overwrite").option(
        "ignoreNullFields", "false"
    ).json(companies_resolved_json)

    # Create and save evaluation metrics - both Parquet and single JSON file
    metrics_data = [
        (
            total_blocks,
            total_raw_companies,
            unique_raw_companies,
            total_resolved_companies,
            unique_resolved_companies,
            reduction_count,
            reduction_percentage,
            overlapping_uuids,
            overlap_percentage,
            unique_source_uuids,
            source_coverage_percentage,
            total_source_uuid_refs,
            valid_source_uuid_count,
            invalid_source_uuid_count,
            error_percentage,
        )
    ]
    metrics_schema = [
        "total_blocks",
        "total_raw_companies",
        "unique_raw_companies",
        "total_resolved_companies",
        "unique_resolved_companies",
        "companies_reduction_count",
        "companies_reduction_percentage",
        "new_uuid_verification_overlap_count",
        "new_uuid_verification_overlap_percentage",
        "unique_source_uuids",
        "source_coverage_percentage",
        "total_source_uuid_refs",
        "valid_source_uuid_count",
        "invalid_source_uuid_count",
        "source_uuid_error_percentage",
    ]
    metrics_df = spark.createDataFrame(metrics_data, metrics_schema)

    metrics_parquet_path = os.path.join(output_path, "er_evaluation_metrics.parquet")
    metrics_json_path = os.path.join(output_path, "er_evaluation_metrics.json")

    logger.info(f"Saving evaluation metrics (Parquet) to {metrics_parquet_path}")
    metrics_df.write.mode("overwrite").parquet(metrics_parquet_path)

    logger.info(f"Saving evaluation metrics (JSON) to {metrics_json_path}")
    metrics_df.coalesce(1).write.mode("overwrite").json(metrics_json_path)

    # Print final summary
    logger.info("\n" + "=" * 60)
    logger.info("ENTITY RESOLUTION EVALUATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Raw companies: {total_raw_companies:,} total, {unique_raw_companies:,} unique")
    logger.info(
        f"Resolved companies: {total_resolved_companies:,} total, {unique_resolved_companies:,} unique"
    )
    logger.info(f"Data reduction: {reduction_count:,} companies ({reduction_percentage:.2f}%)")
    logger.info(
        f"New UUID verification: {overlapping_uuids:,} UUIDs ({overlap_percentage:.2f}%) reuse raw UUIDs"
    )
    logger.info(
        f"Source UUID coverage: {unique_source_uuids:,}/{unique_raw_companies:,} ({source_coverage_percentage:.2f}%)"
    )
    logger.info(
        f"Source UUID validation: {valid_source_uuid_count:,}/{total_source_uuid_refs:,} valid ({error_percentage:.2f}% erroneous)"
    )
    logger.info("Files saved:")
    logger.info(f"  - {companies_resolved_parquet}")
    logger.info(f"  - {companies_resolved_json}")
    logger.info(f"  - {metrics_parquet_path}")
    logger.info(f"  - {metrics_json_path}")
    logger.info("=" * 60)

    spark.stop()

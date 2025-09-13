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
    iteration: int = 1,
    local_mode: Optional[bool] = None,
) -> None:
    """
    Evaluate entity resolution matches by exploding companies and validating source UUIDs.

    This function:
    1. Explodes resolved companies from blocks
    2. Creates companies_resolved.json/parquet files
    3. Reports metrics on data reduction and UUID overlap
    4. Validates source_uuids against ORIGINAL raw companies data
    5. Removes invalid source_uuids and reports error percentage
    6. For iteration 2+, tracks coverage against both original and previous iteration

    Args:
        matches_path: Path to the matches parquet file from ER matching
        raw_companies_path: Path to the ORIGINAL raw companies parquet file (iteration 0)
        output_path: Directory path to save evaluation results
        iteration: Iteration number (1, 2, 3, etc.)
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    # Create SparkSession with appropriate configuration
    spark: SparkSession = get_spark_session(
        app_name="evaluate_er_matches",
        local_mode=local_mode,
    )

    # Format matches_path for reading (should have {iteration} and {format} placeholders)
    matches_parquet_path = matches_path.format(iteration=iteration, format="parquet")
    logger.info(f"Loading matches from {matches_parquet_path}")
    matches_df: DataFrame = spark.read.parquet(matches_parquet_path)

    # Load the ORIGINAL raw companies (always the same, regardless of iteration)
    logger.info(f"Loading ORIGINAL raw companies from {raw_companies_path}")
    original_raw_companies_df: DataFrame = spark.read.parquet(raw_companies_path)

    # For iteration 2+, also load the previous iteration's output for comparison
    previous_iteration_df: Optional[DataFrame] = None
    if iteration > 1:
        prev_iteration = iteration - 1
        prev_iteration_path = output_path.format(iteration=prev_iteration, format="parquet")
        logger.info(
            f"Loading previous iteration ({prev_iteration}) results from {prev_iteration_path}"
        )
        previous_iteration_df = spark.read.parquet(prev_iteration_path)

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

    # Get counts for comparison - original raw first
    total_original_companies = original_raw_companies_df.count()
    unique_original_companies = original_raw_companies_df.select("uuid").distinct().count()
    logger.info(
        f"ORIGINAL raw companies (iteration 0): {total_original_companies:,} total, {unique_original_companies:,} unique"
    )

    # For iteration 2+, get previous iteration counts
    if previous_iteration_df is not None:
        total_prev_companies = previous_iteration_df.count()
        unique_prev_companies = previous_iteration_df.select("uuid").distinct().count()
        logger.info(
            f"Previous iteration ({iteration - 1}) companies: {total_prev_companies:,} total, {unique_prev_companies:,} unique"
        )

    total_resolved_companies = resolved_companies_df.count()
    unique_resolved_companies = resolved_companies_df.select("uuid").distinct().count()
    logger.info(
        f"Resolved companies: {total_resolved_companies:,} total, {unique_resolved_companies:,} unique"
    )

    # Calculate data reduction metrics - from original
    reduction_from_original = total_original_companies - unique_resolved_companies
    reduction_from_original_pct = (
        (reduction_from_original / total_original_companies) * 100
        if total_original_companies > 0
        else 0
    )
    logger.info(
        f"Data reduction from ORIGINAL: {reduction_from_original:,} companies ({reduction_from_original_pct:.2f}%)"
    )

    # For iteration 2+, also calculate reduction from previous iteration
    reduction_from_prev = 0
    reduction_from_prev_pct = 0.0
    if previous_iteration_df is not None:
        reduction_from_prev = unique_prev_companies - unique_resolved_companies
        reduction_from_prev_pct = (
            (reduction_from_prev / unique_prev_companies) * 100 if unique_prev_companies > 0 else 0
        )
        logger.info(
            f"Data reduction from PREVIOUS iteration: {reduction_from_prev:,} companies ({reduction_from_prev_pct:.2f}%)"
        )

    # Verify that resolved companies have new UUIDs (should be 0% overlap with ANY previous data)
    original_uuids = original_raw_companies_df.select("uuid").distinct()
    resolved_uuids = resolved_companies_df.select("uuid").distinct()

    overlapping_with_original = original_uuids.intersect(resolved_uuids).count()
    overlap_with_original_pct = (
        (overlapping_with_original / unique_original_companies) * 100
        if unique_original_companies > 0
        else 0
    )
    logger.info(
        f"UUID overlap with ORIGINAL: {overlapping_with_original:,} ({overlap_with_original_pct:.2f}%) - should be 0%"
    )

    # Check overlap with previous iteration
    overlapping_with_prev = 0
    overlap_with_prev_pct = 0.0
    if previous_iteration_df is not None:
        prev_uuids = previous_iteration_df.select("uuid").distinct()
        overlapping_with_prev = prev_uuids.intersect(resolved_uuids).count()
        overlap_with_prev_pct = (
            (overlapping_with_prev / unique_prev_companies) * 100
            if unique_prev_companies > 0
            else 0
        )
        logger.info(
            f"UUID overlap with PREVIOUS iteration: {overlapping_with_prev:,} ({overlap_with_prev_pct:.2f}%) - should be 0%"
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

    # Get unique source UUIDs and compare with ORIGINAL raw companies
    unique_source_uuids_df = resolved_with_source_uuids.select("source_uuid").distinct()
    unique_source_uuids = unique_source_uuids_df.count()

    # Calculate coverage of ORIGINAL raw companies
    tracked_original_uuids = unique_source_uuids_df.intersect(original_uuids).count()
    original_coverage_pct = (
        (tracked_original_uuids / unique_original_companies) * 100
        if unique_original_companies > 0
        else 0
    )
    logger.info(
        f"Source UUID coverage of ORIGINAL: {tracked_original_uuids:,}/{unique_original_companies:,} ({original_coverage_pct:.2f}%)"
    )

    # For iteration 2+, also check coverage of previous iteration
    tracked_prev_uuids = 0
    prev_coverage_pct = 0.0
    if previous_iteration_df is not None:
        tracked_prev_uuids = unique_source_uuids_df.intersect(prev_uuids).count()
        prev_coverage_pct = (
            (tracked_prev_uuids / unique_prev_companies) * 100 if unique_prev_companies > 0 else 0
        )
        logger.info(
            f"Source UUID coverage of PREVIOUS iteration: {tracked_prev_uuids:,}/{unique_prev_companies:,} ({prev_coverage_pct:.2f}%)"
        )

    # Validate source_uuids against ALL historical UUIDs (original + all previous iterations)
    # Build a union of all valid historical UUIDs
    all_valid_uuids = original_uuids
    if previous_iteration_df is not None:
        # Include UUIDs from previous iteration
        all_valid_uuids = all_valid_uuids.union(prev_uuids).distinct()

    all_valid_uuids_distinct = all_valid_uuids.alias("valid")
    valid_source_uuids = resolved_with_source_uuids.join(
        all_valid_uuids_distinct,
        resolved_with_source_uuids.source_uuid == all_valid_uuids_distinct.uuid,
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

    # Save companies_resolved files - both Parquet and JSON
    # Format the output path with iteration and format
    companies_resolved_parquet = output_path.format(iteration=iteration, format="parquet")
    companies_resolved_json = output_path.format(iteration=iteration, format="json")

    logger.info(f"Saving companies_resolved.parquet to {companies_resolved_parquet}")
    cleaned_resolved_companies.write.mode("overwrite").parquet(companies_resolved_parquet)

    logger.info(f"Saving companies_resolved.json to {companies_resolved_json}")
    cleaned_resolved_companies.coalesce(1).write.mode("overwrite").option(
        "ignoreNullFields", "false"
    ).json(companies_resolved_json)

    # Create and save evaluation metrics - both Parquet and single JSON file
    metrics_data = [
        (
            iteration,
            total_blocks,
            total_original_companies,
            unique_original_companies,
            total_prev_companies if previous_iteration_df is not None else None,
            unique_prev_companies if previous_iteration_df is not None else None,
            total_resolved_companies,
            unique_resolved_companies,
            reduction_from_original,
            reduction_from_original_pct,
            reduction_from_prev if previous_iteration_df is not None else None,
            reduction_from_prev_pct if previous_iteration_df is not None else None,
            overlapping_with_original,
            overlap_with_original_pct,
            overlapping_with_prev if previous_iteration_df is not None else None,
            overlap_with_prev_pct if previous_iteration_df is not None else None,
            unique_source_uuids,
            tracked_original_uuids,
            original_coverage_pct,
            tracked_prev_uuids if previous_iteration_df is not None else None,
            prev_coverage_pct if previous_iteration_df is not None else None,
            total_source_uuid_refs,
            valid_source_uuid_count,
            invalid_source_uuid_count,
            error_percentage,
        )
    ]
    metrics_schema = [
        "iteration",
        "total_blocks",
        "total_original_companies",
        "unique_original_companies",
        "total_prev_iteration_companies",
        "unique_prev_iteration_companies",
        "total_resolved_companies",
        "unique_resolved_companies",
        "reduction_from_original_count",
        "reduction_from_original_pct",
        "reduction_from_prev_count",
        "reduction_from_prev_pct",
        "uuid_overlap_with_original_count",
        "uuid_overlap_with_original_pct",
        "uuid_overlap_with_prev_count",
        "uuid_overlap_with_prev_pct",
        "unique_source_uuids",
        "tracked_original_uuids",
        "original_coverage_pct",
        "tracked_prev_uuids",
        "prev_coverage_pct",
        "total_source_uuid_refs",
        "valid_source_uuid_count",
        "invalid_source_uuid_count",
        "source_uuid_error_pct",
    ]
    metrics_df = spark.createDataFrame(metrics_data, metrics_schema)

    # Get the directory for metrics files
    output_dir = os.path.dirname(output_path)
    metrics_parquet_path = os.path.join(output_dir, "er_evaluation_metrics.parquet")
    metrics_json_path = os.path.join(output_dir, "er_evaluation_metrics.json")

    logger.info(f"Saving evaluation metrics (Parquet) to {metrics_parquet_path}")
    metrics_df.write.mode("overwrite").parquet(metrics_parquet_path)

    logger.info(f"Saving evaluation metrics (JSON) to {metrics_json_path}")
    metrics_df.coalesce(1).write.mode("overwrite").json(metrics_json_path)

    # Print final summary
    logger.info("\n" + "=" * 60)
    logger.info(f"ENTITY RESOLUTION EVALUATION SUMMARY - ITERATION {iteration}")
    logger.info("=" * 60)
    logger.info(
        f"Original raw companies (iteration 0): {total_original_companies:,} total, {unique_original_companies:,} unique"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"Previous iteration ({iteration - 1}) companies: {total_prev_companies:,} total, {unique_prev_companies:,} unique"
        )
    logger.info(
        f"Current iteration ({iteration}) resolved: {total_resolved_companies:,} total, {unique_resolved_companies:,} unique"
    )
    logger.info("")
    logger.info("DATA REDUCTION:")
    logger.info(
        f"  From original: {reduction_from_original:,} companies ({reduction_from_original_pct:.2f}%)"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"  From previous iteration: {reduction_from_prev:,} companies ({reduction_from_prev_pct:.2f}%)"
        )
    logger.info("")
    logger.info("UUID VERIFICATION (should all be 0%):")
    logger.info(
        f"  Overlap with original: {overlapping_with_original:,} UUIDs ({overlap_with_original_pct:.2f}%)"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"  Overlap with previous: {overlapping_with_prev:,} UUIDs ({overlap_with_prev_pct:.2f}%)"
        )
    logger.info("")
    logger.info("SOURCE UUID COVERAGE:")
    logger.info(
        f"  Original companies tracked: {tracked_original_uuids:,}/{unique_original_companies:,} ({original_coverage_pct:.2f}%)"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"  Previous iteration tracked: {tracked_prev_uuids:,}/{unique_prev_companies:,} ({prev_coverage_pct:.2f}%)"
        )
    logger.info(f"  Total unique source_uuids: {unique_source_uuids:,}")
    logger.info("")
    logger.info("SOURCE UUID VALIDATION:")
    logger.info(
        f"  Valid references: {valid_source_uuid_count:,}/{total_source_uuid_refs:,} ({100 - error_percentage:.2f}%)"
    )
    logger.info(
        f"  Invalid references: {invalid_source_uuid_count:,}/{total_source_uuid_refs:,} ({error_percentage:.2f}%)"
    )
    logger.info("Files saved:")
    logger.info(f"  - {companies_resolved_parquet}")
    logger.info(f"  - {companies_resolved_json}")
    logger.info(f"  - {metrics_parquet_path}")
    logger.info(f"  - {metrics_json_path}")
    logger.info("=" * 60)

    spark.stop()

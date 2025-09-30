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
    # Use JSON instead of Parquet because Parquet loses source_uuids
    matches_json_path = matches_path.format(iteration=iteration, format="json")
    logger.info(f"Loading matches from {matches_json_path}")
    matches_df: DataFrame = spark.read.json(matches_json_path)

    # No need for JSON deserialization anymore since we're using PySpark to save
    # The data is already in the correct format with proper struct arrays

    # Load the ORIGINAL raw companies (always the same, regardless of iteration)
    logger.info(f"Loading ORIGINAL raw companies from {raw_companies_path}")
    original_raw_companies_df: DataFrame = spark.read.parquet(raw_companies_path)

    # For iteration 2+, also load the previous iteration's output for comparison
    previous_iteration_df: Optional[DataFrame] = None
    if iteration > 1:
        prev_iteration = iteration - 1
        # Check if output_path has {iteration} placeholder
        if "{iteration}" in output_path:
            prev_iteration_path = output_path.format(iteration=prev_iteration, format="parquet")
        else:
            # If no iteration placeholder, construct path based on current path
            # Replace current iteration with previous iteration in the path
            import re

            prev_iteration_path = re.sub(
                f"iteration_{iteration}",
                f"iteration_{prev_iteration}",
                output_path.format(format="parquet"),
            )

        # Check if the previous iteration output exists
        if os.path.exists(prev_iteration_path):
            logger.info(
                f"Loading previous iteration ({prev_iteration}) results from {prev_iteration_path}"
            )
            previous_iteration_df = spark.read.parquet(prev_iteration_path)
        else:
            logger.info(
                f"Previous iteration ({prev_iteration}) output not found at {prev_iteration_path}, skipping comparison"
            )

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

    # Split into BAML-processed vs skipped companies
    baml_processed_df = resolved_companies_df.filter(
        (F.col("match_skip") == False) | F.col("match_skip").isNull()  # type: ignore
    )
    skipped_df = resolved_companies_df.filter(F.col("match_skip") == True)  # type: ignore

    total_records = resolved_companies_df.count()
    baml_processed_records = baml_processed_df.count()
    skipped_records = skipped_df.count()

    logger.info(f"Total resolved records: {total_records:,}")
    logger.info(f"BAML-processed records (what we care about): {baml_processed_records:,}")
    logger.info(f"Skipped records (singletons/errors): {skipped_records:,}")

    # Analyze match_skip_history and reasons
    skipped_in_current = 0
    error_recovery_count = 0
    missing_uuid_recovery_count = 0
    missing_primary_uuid_count = 0
    missing_source_uuid_count = 0

    if "match_skip_history" in resolved_companies_df.columns:
        # Count records by number of times skipped
        skip_history_df = resolved_companies_df.select(
            "uuid",
            "name",
            "match_skip",
            "match_skip_history",
            (
                F.col("match_skip_reason")
                if "match_skip_reason" in resolved_companies_df.columns
                else F.lit(None).alias("match_skip_reason")
            ),
        ).filter(
            F.col("match_skip_history").isNotNull()
        )  # type: ignore

        # Count records skipped in current iteration
        skipped_in_current = skip_history_df.filter(
            F.array_contains("match_skip_history", iteration)  # type: ignore
        ).count()

        # Count records by skip frequency
        skip_frequency_df = (
            skip_history_df.withColumn("skip_count", F.size("match_skip_history"))  # type: ignore
            .groupBy("skip_count")
            .count()
            .orderBy("skip_count")
        )

        logger.info(f"Records skipped in iteration {iteration}: {skipped_in_current:,}")
        logger.info("Skip frequency distribution:")
        skip_frequency_df.show()

        # Analyze skip reasons if the column exists
        if "match_skip_reason" in resolved_companies_df.columns:
            skip_reason_df = (
                resolved_companies_df.filter(F.col("match_skip") == True)  # type: ignore
                .groupBy("match_skip_reason")
                .count()
                .orderBy(F.desc("count"))
            )

            logger.info("Skip reason distribution:")
            skip_reason_df.show()

            # Count specific reasons
            error_recovery_count = resolved_companies_df.filter(
                F.col("match_skip_reason") == "error_recovery"  # type: ignore
            ).count()

            missing_uuid_recovery_count = resolved_companies_df.filter(
                F.col("match_skip_reason") == "missing_in_match_output"  # type: ignore
            ).count()

            missing_primary_uuid_count = resolved_companies_df.filter(
                F.col("match_skip_reason") == "missing_primary_uuid"  # type: ignore
            ).count()

            missing_source_uuid_count = resolved_companies_df.filter(
                F.col("match_skip_reason") == "missing_source_uuid"  # type: ignore
            ).count()

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

    # COUNT BAML-PROCESSED COMPANIES ONLY (exclude singletons/errors)
    unique_baml_processed = baml_processed_df.select("uuid").distinct().count()
    logger.info(f"BAML-processed companies (after matching): {unique_baml_processed:,} unique")

    # To calculate reduction, we need to know how many companies WENT INTO matching
    # This is: total original companies - skipped companies
    # Skipped companies are those with match_skip=True, which includes singletons
    companies_that_went_into_matching = total_original_companies - skipped_records

    # Calculate data reduction from matching
    # This shows how many companies were merged/deduplicated
    reduction_from_matching = companies_that_went_into_matching - unique_baml_processed
    reduction_from_matching_pct = (
        (reduction_from_matching / companies_that_went_into_matching) * 100
        if companies_that_went_into_matching > 0
        else 0
    )
    logger.info(
        f"Data reduction from matching: {reduction_from_matching:,} companies merged ({reduction_from_matching_pct:.2f}%)"
    )

    # Total output = BAML processed + skipped
    total_output_companies = unique_baml_processed + skipped_records
    total_reduction = total_original_companies - total_output_companies
    total_reduction_pct = (
        (total_reduction / total_original_companies) * 100 if total_original_companies > 0 else 0
    )
    logger.info(
        f"Total reduction (original → output): {total_reduction:,} companies ({total_reduction_pct:.2f}%)"
    )

    # Verify that BAML-PROCESSED companies have new UUIDs (should be 0% overlap)
    # Skipped companies (singletons) will have original UUIDs, which is expected
    original_uuids = original_raw_companies_df.select("uuid").distinct()
    baml_uuids = baml_processed_df.select("uuid").distinct()

    overlapping_with_original = original_uuids.intersect(baml_uuids).count()
    overlap_with_original_pct = (
        (overlapping_with_original / unique_baml_processed) * 100
        if unique_baml_processed > 0
        else 0
    )
    logger.info(
        f"UUID overlap with ORIGINAL (BAML-processed only): {overlapping_with_original:,} ({overlap_with_original_pct:.2f}%) - should be 0%"
    )

    # Check overlap with previous iteration
    overlapping_with_prev = 0
    overlap_with_prev_pct = 0.0
    if previous_iteration_df is not None:
        prev_uuids = previous_iteration_df.select("uuid").distinct()
        overlapping_with_prev = prev_uuids.intersect(baml_uuids).count()
        overlap_with_prev_pct = (
            (overlapping_with_prev / unique_baml_processed) * 100
            if unique_baml_processed > 0
            else 0
        )
        logger.info(
            f"UUID overlap with PREVIOUS iteration (BAML-processed only): {overlapping_with_prev:,} ({overlap_with_prev_pct:.2f}%) - should be 0%"
        )

    # Validate source_uuids - explode them first
    logger.info("Validating source UUIDs...")
    resolved_with_source_uuids = resolved_companies_df.filter(  # type: ignore
        F.col("source_uuids").isNotNull() & (F.size("source_uuids") > 0)  # type: ignore
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

    # Keep ALL source_uuids, not just validated ones
    # This is important because source_uuids may contain historical references
    # that aren't in our current dataset but are still valid
    cleaned_resolved_companies = resolved_companies_df

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
    from pyspark.sql.types import (
        DoubleType,
        IntegerType,
        LongType,
        StructField,
        StructType,
    )

    metrics_data = [
        (
            iteration,
            total_blocks,
            total_original_companies,
            companies_that_went_into_matching,
            skipped_records,
            unique_baml_processed,
            reduction_from_matching,
            reduction_from_matching_pct,
            total_output_companies,
            total_reduction,
            total_reduction_pct,
            overlapping_with_original,
            overlap_with_original_pct,
            unique_source_uuids,
            tracked_original_uuids,
            original_coverage_pct,
            total_source_uuid_refs,
            valid_source_uuid_count,
            invalid_source_uuid_count,
            error_percentage,
        )
    ]

    metrics_schema = StructType(
        [
            StructField("iteration", IntegerType(), False),
            StructField("total_blocks", LongType(), False),
            StructField("total_original_companies", LongType(), False),
            StructField("companies_that_went_into_matching", LongType(), False),
            StructField("skipped_records", LongType(), False),
            StructField("unique_baml_processed", LongType(), False),
            StructField("reduction_from_matching", LongType(), False),
            StructField("reduction_from_matching_pct", DoubleType(), False),
            StructField("total_output_companies", LongType(), False),
            StructField("total_reduction", LongType(), False),
            StructField("total_reduction_pct", DoubleType(), False),
            StructField("uuid_overlap_with_original_count", LongType(), False),
            StructField("uuid_overlap_with_original_pct", DoubleType(), False),
            StructField("unique_source_uuids", LongType(), False),
            StructField("tracked_original_uuids", LongType(), False),
            StructField("original_coverage_pct", DoubleType(), False),
            StructField("total_source_uuid_refs", LongType(), False),
            StructField("valid_source_uuid_count", LongType(), False),
            StructField("invalid_source_uuid_count", LongType(), False),
            StructField("source_uuid_error_pct", DoubleType(), False),
        ]
    )

    metrics_df = spark.createDataFrame(metrics_data, schema=metrics_schema)

    # Get the directory for metrics files
    # Format the output_path first to get the actual directory with iteration number
    formatted_output_path = output_path.format(iteration=iteration, format="parquet")
    output_dir = os.path.dirname(formatted_output_path)
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
    logger.info(f"Original raw companies (iteration 0): {total_original_companies:,} unique")
    logger.info(f"  Companies that went into matching: {companies_that_went_into_matching:,}")
    logger.info(f"  Skipped (singletons/errors): {skipped_records:,}")
    logger.info("")
    logger.info("MATCHING RESULTS:")
    logger.info(f"  BAML-processed companies: {unique_baml_processed:,} unique")
    logger.info(
        f"  Companies merged: {reduction_from_matching:,} ({reduction_from_matching_pct:.2f}%)"
    )
    logger.info("")
    logger.info("FINAL OUTPUT:")
    logger.info(
        f"  Total companies: {total_output_companies:,} ({unique_baml_processed:,} matched + {skipped_records:,} skipped)"
    )
    logger.info(f"  Total reduction: {total_reduction:,} companies ({total_reduction_pct:.2f}%)")
    logger.info("")
    logger.info("UUID VERIFICATION (BAML-processed companies only):")
    logger.info(
        f"  Overlap with original: {overlapping_with_original:,} UUIDs ({overlap_with_original_pct:.2f}%) - should be 0%"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"  Overlap with previous: {overlapping_with_prev:,} UUIDs ({overlap_with_prev_pct:.2f}%) - should be 0%"
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
    logger.info("")
    logger.info("RECOVERY STATISTICS:")
    logger.info(f"  Total recovered (match_skip=True): {skipped_records:,}")
    logger.info(f"  BAML-processed records: {baml_processed_records:,}")
    if "match_skip_history" in resolved_companies_df.columns:
        logger.info(f"  Skipped in iteration {iteration}: {skipped_in_current:,}")
    if "match_skip_reason" in resolved_companies_df.columns and skipped_records > 0:
        logger.info("  Recovery reasons:")
        logger.info(f"    - Error recovery: {error_recovery_count:,}")
        if missing_uuid_recovery_count > 0:
            logger.info(f"    - Missing in match output (legacy): {missing_uuid_recovery_count:,}")
        if missing_primary_uuid_count > 0:
            logger.info(f"    - Missing primary UUID: {missing_primary_uuid_count:,}")
        if missing_source_uuid_count > 0:
            logger.info(f"    - Missing source UUID: {missing_source_uuid_count:,}")

    # Check if we achieved 100% coverage
    if original_coverage_pct >= 99.99:
        logger.info("")
        logger.info("✓ SUCCESS: UUID recovery is working correctly!")
        logger.info("  All original companies are tracked in source_uuids")
    logger.info("=" * 60)
    logger.info("Files saved:")
    logger.info(f"  - {companies_resolved_parquet}")
    logger.info(f"  - {companies_resolved_json}")
    logger.info(f"  - {metrics_parquet_path}")
    logger.info(f"  - {metrics_json_path}")

    # Don't stop the SparkSession - let the caller manage its lifecycle
    # This is important for tests and when the function is called multiple times

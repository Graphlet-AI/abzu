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
from abzu.spark.schemas import get_company_spark_schema, get_matches_schema

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
    2. Creates companies_resolved.parquet files
    3. Reports metrics on data reduction and UUID overlap
    4. Validates source_uuids against ORIGINAL raw companies data
    5. Removes invalid source_uuids and reports error percentage
    6. For iteration 2+, tracks coverage against both original and previous iteration

    Args:
        matches_path: Path to matches.jsonl from the ER match step
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

    # Format matches_path for reading (should have {iteration} placeholder)
    matches_jsonl_path = matches_path.format(iteration=iteration)

    # Check if required input files exist
    if not os.path.exists(matches_jsonl_path):
        error_msg = (
            f"Matches file not found: {matches_jsonl_path}\n\n"
            f"The evaluation step requires output from the match step.\n"
            f"Please run the match step first:\n"
            f"  abzu process er match --iteration {iteration}\n\n"
            f"Or run the complete pipeline:\n"
            f"  abzu process er all --iteration {iteration}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not os.path.exists(raw_companies_path):
        error_msg = (
            f"Raw companies file not found: {raw_companies_path}\n\n"
            f"The evaluation step requires the original raw companies data.\n"
            f"Please ensure you have run the KG raw processing step:\n"
            f"  abzu process kg raw"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Loading matches from {matches_jsonl_path}")
    # Read block records from matches.jsonl with explicit schema to enforce BAML types
    blocks_df: DataFrame = spark.read.json(matches_jsonl_path, schema=get_matches_schema())

    # Explode resolved_companies from blocks to get individual companies
    logger.info("Exploding resolved_companies from blocks...")
    matches_df = blocks_df.select(F.explode("resolved_companies").alias("company")).select(
        "company.*"
    )

    # Load the ORIGINAL raw companies (always the same, regardless of iteration)
    logger.info(f"Loading ORIGINAL raw companies from {raw_companies_path}")
    if raw_companies_path.endswith(".parquet") or raw_companies_path.endswith(".parquet/"):
        original_raw_companies_df: DataFrame = spark.read.parquet(raw_companies_path)
    else:
        original_raw_companies_df = spark.read.json(raw_companies_path)

    # For iteration 2+, also load the previous iteration's output for comparison
    previous_iteration_df: Optional[DataFrame] = None
    if iteration > 1:
        prev_iteration = iteration - 1
        # Check if output_path has {iteration} placeholder
        if "{iteration}" in output_path:
            prev_iteration_path = output_path.format(iteration=prev_iteration)
        else:
            # If no iteration placeholder, construct path based on current path
            # Replace current iteration with previous iteration in the path
            import re

            prev_iteration_path = re.sub(
                f"iteration_{iteration}",
                f"iteration_{prev_iteration}",
                output_path,
            )

        # Check if the previous iteration output exists
        if os.path.exists(prev_iteration_path):
            logger.info(
                f"Loading previous iteration ({prev_iteration}) results from {prev_iteration_path}"
            )
            company_schema = get_company_spark_schema()
            previous_iteration_df = spark.read.schema(company_schema).parquet(prev_iteration_path)
        else:
            logger.info(
                f"Previous iteration ({prev_iteration}) output not found at {prev_iteration_path}, skipping comparison"
            )

    # Calculate the actual input to THIS iteration (not the raw original)
    # For iteration 1: input is the raw companies
    # For iteration 2+: input is the previous iteration's output
    if iteration == 1 or previous_iteration_df is None:
        iteration_input_companies = original_raw_companies_df.count()
    else:
        iteration_input_companies = previous_iteration_df.count()

    total_blocks = blocks_df.count()
    total_companies = matches_df.count()
    logger.info(f"Loaded {total_blocks:,} blocks containing {total_companies:,} resolved companies")

    # Show sample of matches data
    if logger.isEnabledFor(logging.DEBUG):
        logger.info("Sample input data:")
        matches_df.show(3, truncate=False)

    # Input is exploded resolved_companies from match step
    logger.info("Using resolved companies from match step...")

    # Deduplicate exact copies before any counting/evaluation
    pre_dedup_count = matches_df.count()
    resolved_companies_df = matches_df.distinct()
    post_dedup_count = resolved_companies_df.count()
    exact_duplicates_removed = pre_dedup_count - post_dedup_count
    if exact_duplicates_removed > 0:
        logger.info(
            f"Removed {exact_duplicates_removed:,} exact duplicate records "
            f"({pre_dedup_count:,} → {post_dedup_count:,})"
        )

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
    singleton_block_count = 0

    if "match_skip_history" in resolved_companies_df.columns:
        # Count records by number of times skipped
        # Select columns conditionally based on what exists
        select_cols = ["uuid", "name", "match_skip", "match_skip_history"]
        if "match_skip_reason" in resolved_companies_df.columns:
            select_cols.append("match_skip_reason")

        skip_history_df = resolved_companies_df.select(*select_cols).filter(
            F.col("match_skip_history").isNotNull()  # type: ignore[call-arg]
        )

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

            singleton_block_count = resolved_companies_df.filter(
                F.col("match_skip_reason") == "singleton_block"  # type: ignore
            ).count()

    # Get counts for comparison - original raw first
    total_original_companies = original_raw_companies_df.count()
    unique_original_companies = original_raw_companies_df.select("uuid").distinct().count()
    logger.info(
        f"ORIGINAL raw companies (before matching): {total_original_companies:,} total, {unique_original_companies:,} unique"
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

    # Just plain deduplicate records
    more_unique_baml_processed = baml_processed_df.distinct().count()
    logger.info(
        f"Deduplicated BAML-processed companies to ensure uniqueness: {more_unique_baml_processed:,} unique"
    )

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
        else 0.0
    )
    logger.info(
        f"Data reduction from matching: {reduction_from_matching:,} companies merged ({reduction_from_matching_pct:.2f}%)"
    )

    # Calculate IDs dropped by BAML (went in but didn't come out)
    ids_dropped_by_baml = missing_uuid_recovery_count
    ids_dropped_pct = (
        (ids_dropped_by_baml / companies_that_went_into_matching) * 100
        if companies_that_went_into_matching > 0
        else 0.0
    )
    logger.info(
        f"IDs dropped by BAML: {ids_dropped_by_baml:,} ({ids_dropped_pct:.2f}%) - recovered via UUID tracking"
    )

    # Total output = BAML processed + skipped
    total_output_companies = unique_baml_processed + skipped_records
    total_reduction = total_original_companies - total_output_companies
    total_reduction_pct = (
        (total_reduction / total_original_companies) * 100 if total_original_companies > 0 else 0.0
    )
    logger.info(
        f"Total reduction (original → output): {total_reduction:,} companies ({total_reduction_pct:.2f}%)"
    )

    # Skipped companies (singletons) will have original UUIDs, which is expected
    original_uuids = original_raw_companies_df.select("uuid").distinct()
    baml_uuids = baml_processed_df.select("uuid").distinct()

    overlapping_with_original = original_uuids.intersect(baml_uuids).count()
    overlap_with_original_pct = (
        (overlapping_with_original / unique_baml_processed) * 100
        if unique_baml_processed > 0
        else 0.0
    )
    logger.info(
        f"UUID overlap with ORIGINAL (BAML-processed only): {overlapping_with_original:,} ({overlap_with_original_pct:.2f}%)"
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
            else 0.0
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
        else 0.0
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
            (tracked_prev_uuids / unique_prev_companies) * 100 if unique_prev_companies > 0 else 0.0
        )
        logger.info(
            f"Source UUID coverage of PREVIOUS iteration: {tracked_prev_uuids:,}/{unique_prev_companies:,} ({prev_coverage_pct:.2f}%)"
        )

    # Validate source_uuids against ALL historical UUIDs (original + all previous iterations)
    # Build a union of all valid historical UUIDs
    all_valid_uuids = original_uuids

    # Load UUIDs from ALL previous iterations (not just immediate previous)
    # This ensures we can validate source_uuids that chain through multiple iterations
    for prev_iter in range(1, iteration):
        prev_iter_path = output_path.format(iteration=prev_iter)
        if os.path.exists(prev_iter_path):
            logger.debug(f"Loading UUIDs from iteration {prev_iter} for validation")
            prev_iter_df = spark.read.parquet(prev_iter_path)
            prev_iter_uuids = prev_iter_df.select("uuid").distinct()
            all_valid_uuids = all_valid_uuids.union(prev_iter_uuids).distinct()
        else:
            logger.debug(f"Iteration {prev_iter} output not found at {prev_iter_path}, skipping")

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

    # Save companies_resolved file as Parquet
    companies_resolved_parquet = output_path.format(iteration=iteration)

    logger.info(f"Saving companies_resolved.parquet to {companies_resolved_parquet}")
    cleaned_resolved_companies.coalesce(1).write.mode("overwrite").parquet(
        companies_resolved_parquet
    )

    # Create and save evaluation metrics as Parquet
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
            iteration_input_companies,
            total_original_companies,
            companies_that_went_into_matching,
            skipped_records,
            unique_baml_processed,
            reduction_from_matching,
            reduction_from_matching_pct,
            ids_dropped_by_baml,
            ids_dropped_pct,
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
            StructField("iteration_input_companies", LongType(), False),
            StructField("total_original_companies", LongType(), False),
            StructField("companies_that_went_into_matching", LongType(), False),
            StructField("skipped_records", LongType(), False),
            StructField("unique_baml_processed", LongType(), False),
            StructField("reduction_from_matching", LongType(), False),
            StructField("reduction_from_matching_pct", DoubleType(), False),
            StructField("ids_dropped_by_baml", LongType(), False),
            StructField("ids_dropped_by_baml_pct", DoubleType(), False),
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
    formatted_output_path = output_path.format(iteration=iteration)
    output_dir = os.path.dirname(formatted_output_path)
    metrics_parquet_path = os.path.join(output_dir, "er_evaluation_metrics.parquet")

    logger.info(f"Saving evaluation metrics to {metrics_parquet_path}")
    metrics_df.coalesce(1).write.mode("overwrite").parquet(metrics_parquet_path)

    # Print final summary
    logger.info("\n" + "=" * 60)
    logger.info(f"ENTITY RESOLUTION EVALUATION SUMMARY - ITERATION {iteration}")
    logger.info("=" * 60)
    logger.info("WHAT IS EVALUATION?")
    logger.info("  Validates matching results, tracks UUID lineage, and ensures no data loss")
    logger.info("  Explodes resolved companies from blocks into final dataset")
    logger.info("")
    logger.info("INPUT/OUTPUT SUMMARY:")
    logger.info(f"  Original companies (before matching): {total_original_companies:,} unique")
    logger.info(f"    ├─ Went into matching: {companies_that_went_into_matching:,}")
    logger.info(f"    └─ Skipped (singletons/errors): {skipped_records:,}")
    logger.info(f"  Final output companies: {total_output_companies:,} unique")
    logger.info(f"    ├─ BAML-processed: {unique_baml_processed:,}")
    logger.info(f"    └─ Pass-through (skipped): {skipped_records:,}")
    logger.info(f"  Total reduction: {total_reduction:,} companies ({total_reduction_pct:.2f}%)")
    logger.info("")
    logger.info("MATCHING EFFECTIVENESS:")
    logger.info(
        f"  Companies merged by BAML: {reduction_from_matching:,} / {companies_that_went_into_matching:,} ({reduction_from_matching_pct:.2f}%)"
    )
    logger.info(
        f"  IDs dropped by BAML: {ids_dropped_by_baml:,} ({ids_dropped_pct:.2f}%) → recovered via UUID tracking ✓"
    )
    logger.info("")
    logger.info("UUID VERIFICATION:")
    uuid_status = "✓ PASS" if overlap_with_original_pct < 1.0 else "✗ FAIL"
    logger.info(
        f"  BAML-processed companies vs original: {overlapping_with_original:,} overlap ({overlap_with_original_pct:.2f}%) {uuid_status}"
    )
    logger.info("    └─ Should be 0% (new UUIDs for resolved companies)")
    if previous_iteration_df is not None:
        prev_uuid_status = "✓ PASS" if overlap_with_prev_pct < 1.0 else "✗ FAIL"
        logger.info(
            f"  BAML-processed companies vs previous iteration: {overlapping_with_prev:,} overlap ({overlap_with_prev_pct:.2f}%) {prev_uuid_status}"
        )
        logger.info("    └─ Should be 0% (new UUIDs each iteration)")
    logger.info("")
    logger.info("SOURCE UUID TRACKING:")
    logger.info(f"  Total unique source_uuids: {unique_source_uuids:,}")
    logger.info(
        f"  Total source_uuid references: {total_source_uuid_refs:,} (avg {total_source_uuid_refs / total_output_companies:.1f} per company)"
    )
    coverage_status = "✓ PASS" if original_coverage_pct >= 99.99 else "✗ FAIL"
    logger.info(
        f"  Original companies tracked: {tracked_original_uuids:,} / {unique_original_companies:,} ({original_coverage_pct:.2f}%) {coverage_status}"
    )
    if previous_iteration_df is not None:
        logger.info(
            f"  Previous iteration tracked: {tracked_prev_uuids:,} / {unique_prev_companies:,} ({prev_coverage_pct:.2f}%)"
        )
    logger.info("")
    logger.info("SOURCE UUID VALIDATION:")
    validation_status = "✓ PASS" if error_percentage < 0.01 else "✗ FAIL"
    logger.info(
        f"  Valid references: {valid_source_uuid_count:,} / {total_source_uuid_refs:,} ({100 - error_percentage:.2f}%) {validation_status}"
    )
    if invalid_source_uuid_count > 0:
        logger.info(
            f"  Invalid references: {invalid_source_uuid_count:,} / {total_source_uuid_refs:,} ({error_percentage:.2f}%)"
        )
    logger.info("")
    logger.info("RECOVERY STATISTICS:")
    logger.info(f"  Skipped in iteration {iteration}: {skipped_in_current:,} / {total_records:,}")
    if "match_skip_reason" in resolved_companies_df.columns and skipped_records > 0:
        logger.info("  Recovery breakdown:")
        logger.info(f"    ├─ Singleton blocks: {singleton_block_count:,}")
        if error_recovery_count > 0:
            logger.info(f"    ├─ API error recovery: {error_recovery_count:,}")
        if missing_uuid_recovery_count > 0:
            logger.info(f"    ├─ BAML dropped output: {missing_uuid_recovery_count:,}")
        if missing_primary_uuid_count > 0:
            logger.info(f"    ├─ Missing primary UUID: {missing_primary_uuid_count:,}")
        if missing_source_uuid_count > 0:
            logger.info(f"    └─ Missing source UUID: {missing_source_uuid_count:,}")

    # Overall status assessment
    logger.info("")
    all_checks_pass = (
        original_coverage_pct >= 99.99  # All original companies tracked
        and error_percentage < 0.01  # No invalid UUID references
        and overlap_with_original_pct < 1.0  # New UUIDs generated (if not, this is a bug)
    )
    if all_checks_pass:
        logger.info("✓ SUCCESS: All validation checks passed!")
        logger.info("  └─ UUID tracking working correctly")
        logger.info("  └─ No data loss detected")
        logger.info("  └─ Resolved companies have new UUIDs")
    else:
        logger.info("✗ WARNING: Some validation checks failed")
        if original_coverage_pct < 99.99:
            logger.info(f"  └─ Only {original_coverage_pct:.2f}% of original companies tracked")
        if error_percentage >= 0.01:
            logger.info(f"  └─ {error_percentage:.2f}% invalid UUID references detected")
        if overlap_with_original_pct >= 1.0:
            logger.info("  └─ Resolved companies reusing original UUIDs (BUG!)")
    logger.info("")
    logger.info("OUTPUT FILES:")
    logger.info(f"  Resolved companies: {companies_resolved_parquet}")
    logger.info(f"  Evaluation metrics: {metrics_parquet_path}")
    logger.info("=" * 60)

    # Don't stop the SparkSession - let the caller manage its lifecycle
    # This is important for tests and when the function is called multiple times

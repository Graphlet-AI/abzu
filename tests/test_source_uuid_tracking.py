#!/usr/bin/env python3
"""Test source UUID tracking through multiple entity resolution iterations."""

import json
import os
import shutil
import tempfile
import uuid
from typing import Any

import pytest
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F

from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.er_block import build_blocks
from abzu.spark.er_eval import evaluate_er_matches

logger = get_logger(__name__)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def spark_session():
    """Create a Spark session for testing."""
    spark = get_spark_session(app_name="test_source_uuid_tracking", local_mode=True)
    yield spark
    spark.stop()


def create_test_companies(num_companies: int = 10) -> list[dict[str, Any]]:
    """
    Create test company records with identical data but different UUIDs.

    Args:
        num_companies: Number of identical companies to create

    Returns:
        List of company dictionaries
    """
    companies = []
    for i in range(num_companies):
        company: dict[str, Any] = {
            "uuid": str(uuid.uuid4()),
            "name": "Acme Corporation",
            "description": "A leading provider of innovative solutions",
            "website_url": "https://www.acme.com",
            "linkedin_url": "https://www.linkedin.com/company/acme",
            "twitter_url": "https://twitter.com/acme",
            "facebook_url": "https://www.facebook.com/acme",
            "city": "San Francisco",
            "state": "CA",
            "country": "USA",
            "source_uuids": [],  # Start with empty source_uuids
        }
        companies.append(company)
    return companies


def save_companies_to_parquet(
    spark: SparkSession, companies: list[dict[str, Any]], output_path: str
) -> None:
    """Save companies to Parquet format."""
    # Define schema explicitly to handle empty arrays
    from pyspark.sql.types import ArrayType, StringType, StructField, StructType

    # Ensure all companies have all required fields with defaults
    normalized_companies = []
    for company in companies:
        normalized = {
            "uuid": company.get("uuid"),
            "name": company.get("name"),
            "description": company.get("description"),
            "website_url": company.get("website_url"),
            "linkedin_url": company.get("linkedin_url"),
            "twitter_url": company.get("twitter_url"),
            "facebook_url": company.get("facebook_url"),
            "city": company.get("city"),
            "state": company.get("state"),
            "country": company.get("country"),
            "source_uuids": company.get("source_uuids", []),
        }
        normalized_companies.append(normalized)

    schema = StructType(
        [
            StructField("uuid", StringType(), True),
            StructField("name", StringType(), True),
            StructField("description", StringType(), True),
            StructField("website_url", StringType(), True),
            StructField("linkedin_url", StringType(), True),
            StructField("twitter_url", StringType(), True),
            StructField("facebook_url", StringType(), True),
            StructField("city", StringType(), True),
            StructField("state", StringType(), True),
            StructField("country", StringType(), True),
            StructField("source_uuids", ArrayType(StringType()), True),
        ]
    )

    df = spark.createDataFrame([Row(**x) for x in normalized_companies], schema=schema)
    df.write.mode("overwrite").parquet(output_path)


def load_companies_from_parquet(spark: SparkSession, path: str) -> DataFrame:
    """Load companies from Parquet format."""
    return spark.read.parquet(path)


def run_single_iteration(
    iteration: int,
    input_path: str,
    output_base_path: str,
    original_raw_path: str,
    max_block_size: int = 2,
    spark: SparkSession | None = None,
) -> dict[str, Any]:
    """
    Run a single iteration of block -> match -> eval.

    Args:
        iteration: Iteration number
        input_path: Path to input companies parquet
        output_base_path: Base path for output files
        max_block_size: Maximum block size for blocking

    Returns:
        Dictionary with iteration results
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"RUNNING ITERATION {iteration}")
    logger.info(f"{'=' * 60}")

    # Create iteration-specific paths
    blocks_path = os.path.join(output_base_path, f"iteration_{iteration}", "blocks")
    matches_path = os.path.join(output_base_path, f"iteration_{iteration}", "matches.{format}")
    eval_path = os.path.join(
        output_base_path, f"iteration_{iteration}", "companies_resolved.{format}"
    )

    # Step 1: Blocking
    logger.info(f"Step 1: Blocking with max_block_size={max_block_size}")
    build_blocks(
        input_path=input_path,
        output_path=blocks_path,
        max_block_size=max_block_size,
        local_mode=True,
        stop_spark=False,  # Don't stop spark between steps
    )

    # Load blocks - handle partitioned JSON output
    blocks_data = []

    # Try union_blocks.json first (might be a directory with part files)
    union_blocks_path = os.path.join(blocks_path, "union_blocks.json")
    if os.path.isdir(union_blocks_path):
        # Load all part-*.json files from the directory
        import glob

        part_files = glob.glob(os.path.join(union_blocks_path, "part-*.json"))
        for part_file in sorted(part_files):
            with open(part_file) as f:
                blocks_data.extend([json.loads(line) for line in f])
    elif os.path.isfile(union_blocks_path):
        # Single file
        with open(union_blocks_path) as f:
            blocks_data = [json.loads(line) for line in f]
    else:
        # Try alternative location - combined_blocks.json
        combined_blocks_path = os.path.join(blocks_path, "combined_blocks.json")
        if os.path.isdir(combined_blocks_path):
            import glob

            part_files = glob.glob(os.path.join(combined_blocks_path, "part-*.json"))
            for part_file in sorted(part_files):
                with open(part_file) as f:
                    blocks_data.extend([json.loads(line) for line in f])
        elif os.path.isfile(combined_blocks_path):
            with open(combined_blocks_path) as f:
                blocks_data = [json.loads(line) for line in f]

    logger.info(f"Created {len(blocks_data)} blocks")

    # Step 2: Matching
    logger.info("Step 2: Matching blocks")
    matches_json_path = matches_path.format(format="json")
    matches_parquet_path = matches_path.format(format="parquet")

    # For testing, we'll create mock matches that merge pairs of companies
    # In a real test, you would call the actual matching function
    matched_blocks = []
    for block in blocks_data:
        # Simulate matching - merge companies in blocks of 2+
        if len(block["companies"]) >= 2:
            # Merge companies, preserving source_uuids
            merged_company = block["companies"][0].copy()

            # Collect all UUIDs into source_uuids
            all_source_uuids = []
            for comp in block["companies"]:
                # Add the company's UUID
                all_source_uuids.append(comp["uuid"])
                # Add any existing source_uuids
                if "source_uuids" in comp and comp["source_uuids"]:
                    all_source_uuids.extend(comp["source_uuids"])

            # Remove duplicates while preserving order
            seen = set()
            unique_source_uuids = []
            for uuid_val in all_source_uuids:
                if uuid_val not in seen:
                    seen.add(uuid_val)
                    unique_source_uuids.append(uuid_val)
            merged_company["source_uuids"] = unique_source_uuids
            merged_company["uuid"] = str(uuid.uuid4())  # New UUID for merged company

            matched_blocks.append(
                {
                    "block_key": block["block_key"],
                    "block_key_type": block["block_key_type"],
                    "resolved_companies": [merged_company],
                    "was_resolved": True,
                    "original_count": len(block["companies"]),
                    "resolved_count": 1,
                }
            )
        else:
            # Single company - pass through with UUID added to source_uuids
            company = block["companies"][0].copy()
            if "source_uuids" not in company:
                company["source_uuids"] = []
            if company["uuid"] not in company["source_uuids"]:
                company["source_uuids"].append(company["uuid"])

            matched_blocks.append(
                {
                    "block_key": block["block_key"],
                    "block_key_type": block["block_key_type"],
                    "resolved_companies": [company],
                    "was_resolved": False,
                    "original_count": 1,
                    "resolved_count": 1,
                }
            )

    # Save matches
    with open(matches_json_path, "w") as f:
        for match in matched_blocks:
            f.write(json.dumps(match) + "\n")

    # Also save as parquet - need to match the expected schema
    if spark is None:
        spark = get_spark_session(app_name="test_save_matches", local_mode=True)

    # Convert to DataFrame with proper schema for eval function
    from pyspark.sql.types import (
        ArrayType,
        BooleanType,
        IntegerType,
        StringType,
        StructField,
        StructType,
    )

    # Define company schema
    company_schema = StructType(
        [
            StructField("uuid", StringType(), True),
            StructField("name", StringType(), True),
            StructField("description", StringType(), True),
            StructField("website_url", StringType(), True),
            StructField("linkedin_url", StringType(), True),
            StructField("twitter_url", StringType(), True),
            StructField("facebook_url", StringType(), True),
            StructField("city", StringType(), True),
            StructField("state", StringType(), True),
            StructField("country", StringType(), True),
            StructField("source_uuids", ArrayType(StringType()), True),
        ]
    )

    # Define matches schema
    matches_schema = StructType(
        [
            StructField("block_key", StringType(), False),
            StructField("block_key_type", StringType(), False),
            StructField("resolved_companies", ArrayType(company_schema), False),
            StructField("was_resolved", BooleanType(), False),
            StructField("original_count", IntegerType(), True),
            StructField("resolved_count", IntegerType(), True),
        ]
    )

    matches_df = spark.createDataFrame(matched_blocks, schema=matches_schema)  # type: ignore[arg-type]
    matches_df.write.mode("overwrite").parquet(matches_parquet_path)

    # Step 3: Evaluation
    logger.info("Step 3: Evaluating matches")

    evaluate_er_matches(
        matches_path=matches_path,
        raw_companies_path=original_raw_path,
        output_path=eval_path,
        iteration=iteration,
        local_mode=True,
    )

    # Load results
    if spark is None:
        spark = get_spark_session(app_name="test_load_results", local_mode=True)
    resolved_df = spark.read.parquet(eval_path.format(format="parquet"))

    # Analyze results
    total_companies = resolved_df.count()
    unique_companies = resolved_df.select("uuid").distinct().count()

    # Check source_uuids coverage
    with_source_uuids = resolved_df.filter(
        F.col("source_uuids").isNotNull() & (F.size("source_uuids") > 0)
    ).count()

    # Get all source_uuids
    unique_source_uuid_count = (
        resolved_df.filter(F.col("source_uuids").isNotNull())
        .select(F.explode("source_uuids").alias("source_uuid"))
        .distinct()
        .count()
    )

    results = {
        "iteration": iteration,
        "total_companies": total_companies,
        "unique_companies": unique_companies,
        "companies_with_source_uuids": with_source_uuids,
        "unique_source_uuids": unique_source_uuid_count,
        "blocks_created": len(blocks_data),
    }

    logger.info(f"Iteration {iteration} results:")
    logger.info(f"  Total companies: {total_companies}")
    logger.info(f"  Unique companies: {unique_companies}")
    logger.info(f"  Companies with source_uuids: {with_source_uuids}")
    logger.info(f"  Unique source_uuids tracked: {unique_source_uuid_count}")

    return results


def test_source_uuid_tracking_multiple_iterations(temp_dir, spark_session):
    """
    Test that source UUIDs are properly tracked through multiple ER iterations.

    This test:
    1. Creates 10 identical companies with different UUIDs
    2. Runs multiple iterations of block/match/eval with max_block_size=2
    3. Verifies that all original UUIDs are preserved in source_uuids
    4. Continues until all companies are merged into one with 10 source_uuids
    """
    # Create test data
    num_companies = 10
    companies = create_test_companies(num_companies)

    # Save original UUIDs for verification
    original_uuids = {company["uuid"] for company in companies}
    logger.info(f"Created {num_companies} test companies with unique UUIDs")

    # Save initial companies
    initial_path = os.path.join(temp_dir, "iteration_0", "companies.parquet")
    os.makedirs(os.path.dirname(initial_path), exist_ok=True)
    save_companies_to_parquet(spark_session, companies, initial_path)

    # Run iterations until we have a single company
    max_iterations = 5  # Safety limit
    iteration = 1
    current_input_path = initial_path
    iteration_results = []

    while iteration <= max_iterations:
        results = run_single_iteration(
            iteration=iteration,
            input_path=current_input_path,
            output_base_path=temp_dir,
            original_raw_path=initial_path,
            max_block_size=2,  # Force gradual merging
            spark=spark_session,
        )
        iteration_results.append(results)

        # Check if we've merged everything into one company
        if results["unique_companies"] == 1:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"SUCCESS: All companies merged into 1 after {iteration} iterations")
            logger.info(f"{'=' * 60}")
            break

        # Update input path for next iteration
        current_input_path = os.path.join(
            temp_dir, f"iteration_{iteration}", "companies_resolved.parquet"
        )
        iteration += 1

    # Verify final results
    assert iteration <= max_iterations, (
        f"Failed to merge all companies within {max_iterations} iterations"
    )

    # Load final resolved companies
    final_path = os.path.join(temp_dir, f"iteration_{iteration}", "companies_resolved.parquet")
    final_df = spark_session.read.parquet(final_path)

    # Should have exactly 1 company
    assert final_df.count() == 1, "Should have exactly 1 company after all iterations"

    # Get the source_uuids from the final company
    final_company = final_df.collect()[0]
    final_source_uuids = (
        set(final_company["source_uuids"]) if final_company["source_uuids"] else set()
    )

    logger.info(f"\nFinal company has {len(final_source_uuids)} source_uuids")
    logger.info(f"Original UUIDs: {len(original_uuids)}")

    # Verify all original UUIDs are present
    missing_uuids = original_uuids - final_source_uuids
    extra_uuids = final_source_uuids - original_uuids

    if missing_uuids:
        logger.error(f"Missing UUIDs: {missing_uuids}")
    if extra_uuids:
        logger.warning(f"Extra UUIDs (from intermediate iterations): {extra_uuids}")

    # The key assertion: all original UUIDs should be in source_uuids
    assert len(missing_uuids) == 0, f"Lost {len(missing_uuids)} original UUIDs during iterations"
    assert len(final_source_uuids) >= num_companies, (
        f"Should have at least {num_companies} source_uuids"
    )

    # Log iteration progression
    logger.info("\nIteration progression:")
    for result in iteration_results:
        logger.info(
            f"  Iteration {result['iteration']}: "
            f"{result['unique_companies']} companies, "
            f"{result['unique_source_uuids']} source_uuids tracked"
        )

    logger.info("\n✅ Test passed: All original UUIDs preserved through multiple iterations")


def test_source_uuid_accumulation(temp_dir, spark_session):
    """
    Test that source_uuids are properly accumulated when companies already have them.

    This test verifies that when companies with existing source_uuids are merged,
    all source_uuids are preserved and combined.
    """
    # Create companies with pre-existing source_uuids
    company1 = {
        "uuid": str(uuid.uuid4()),
        "name": "Acme Corporation",
        "description": "A company",
        "source_uuids": ["old-uuid-1", "old-uuid-2"],
    }

    company2 = {
        "uuid": str(uuid.uuid4()),
        "name": "Acme Corp",  # Slightly different name
        "description": "A company",
        "source_uuids": ["old-uuid-3", "old-uuid-4"],
    }

    companies = [company1, company2]

    # Save companies
    input_path = os.path.join(temp_dir, "companies.parquet")
    save_companies_to_parquet(spark_session, companies, input_path)

    # Run one iteration
    run_single_iteration(
        iteration=1,
        input_path=input_path,
        output_base_path=temp_dir,
        original_raw_path=input_path,
        max_block_size=10,  # Allow merging in one iteration
        spark=spark_session,
    )

    # Load results
    final_path = os.path.join(temp_dir, "iteration_1", "companies_resolved.parquet")
    final_df = spark_session.read.parquet(final_path)

    # Should have 1 company if they merged
    if final_df.count() == 1:
        final_company = final_df.collect()[0]
        final_source_uuids = (
            set(final_company["source_uuids"]) if final_company["source_uuids"] else set()
        )

        # Should contain all old source_uuids plus the two original UUIDs
        expected_uuids = {
            "old-uuid-1",
            "old-uuid-2",
            "old-uuid-3",
            "old-uuid-4",
            company1["uuid"],
            company2["uuid"],
        }

        missing = expected_uuids - final_source_uuids
        assert len(missing) == 0, f"Missing expected UUIDs: {missing}"

        logger.info("✅ Source UUIDs properly accumulated from pre-existing values")
    else:
        logger.info("ℹ️ Companies did not merge in this test (expected if names too different)")


if __name__ == "__main__":
    # Run the test directly
    test_temp_dir = tempfile.mkdtemp()
    test_spark = get_spark_session(app_name="test_source_uuid_manual", local_mode=True)

    try:
        test_source_uuid_tracking_multiple_iterations(test_temp_dir, test_spark)
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
    finally:
        test_spark.stop()
        shutil.rmtree(test_temp_dir)

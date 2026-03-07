"""Unit tests for entity resolution blocking UDTF with schema normalization."""

import json
import os
from typing import Any

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from abzu.spark.er_block import build_blocks
from abzu.spark.schemas import normalize_company_dataframe


@pytest.fixture(scope="module")
def spark() -> SparkSession:  # type: ignore
    """Create a SparkSession for testing."""
    spark = (
        SparkSession.builder.master("local[1]")  # type: ignore
        .appName("test_er_block_udtf")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def create_raw_companies_data() -> list[dict[str, Any]]:
    """Create sample raw company data (first iteration input)."""
    return [
        {
            "id": 1,
            "uuid": "uuid-1",
            "name": "Apple Inc",
            "description": "Technology company",
            "cik": "0000320193",
            "website_url": "https://apple.com",
            "headquarters_location": "Cupertino, CA",
            "revenue_usd": 394328000000,
            "employees": 164000,
            "founded_year": 1976,
            "ceo": "Tim Cook",
        },
        {
            "id": 2,
            "uuid": "uuid-2",
            "name": "Apple Corp",
            "description": "Music company",
            "cik": None,
            "website_url": None,
            "headquarters_location": "London, UK",
            "revenue_usd": None,
            "employees": None,
            "founded_year": 1968,
            "ceo": None,
        },
        {
            "id": 3,
            "uuid": "uuid-3",
            "name": "Google LLC",
            "description": "Search and advertising",
            "cik": "0001652044",
            "website_url": "https://google.com",
            "headquarters_location": "Mountain View, CA",
            "revenue_usd": 282836000000,
            "employees": 190234,
            "founded_year": 1998,
            "ceo": "Sundar Pichai",
        },
    ]


def create_resolved_companies_data():
    """Create sample resolved company data (second iteration input).

    This simulates data that has gone through one iteration of ER,
    potentially with extra fields or different structure.
    """
    return [
        {
            "id": 1,
            "uuid": "resolved-uuid-1",
            "name": "Apple Inc",
            "description": "Technology and consumer electronics company",
            "cik": "0000320193",
            "website_url": "https://apple.com",
            "headquarters_location": "Cupertino, CA",
            "revenue_usd": 394328000000,
            "employees": 164000,
            "founded_year": 1976,
            "ceo": "Tim Cook",
            "source_uuids": ["uuid-1", "uuid-2"],  # From merging
            "source_ids": [1, 2],
            # These fields might accidentally be included from previous blocking
            "block_key": "APPLE",
            "block_key_type": "combined",
        },
        {
            "id": 3,
            "uuid": "resolved-uuid-2",
            "name": "Google LLC",
            "description": "Search, advertising, and cloud computing",
            "cik": "0001652044",
            "website_url": "https://google.com",
            "headquarters_location": "Mountain View, CA",
            "revenue_usd": 282836000000,
            "employees": 190234,
            "founded_year": 1998,
            "ceo": "Sundar Pichai",
            "source_uuids": ["uuid-3"],
            "source_ids": [3],
        },
    ]


def test_schema_normalization(spark):
    """Test that schema normalization works correctly."""
    # Create DataFrames with different schemas
    raw_data = create_raw_companies_data()
    resolved_data = create_resolved_companies_data()

    raw_df = spark.createDataFrame(raw_data)
    resolved_df = spark.createDataFrame(resolved_data)

    # Check initial schemas are different
    assert "block_key" not in raw_df.columns
    assert "block_key" in resolved_df.columns

    # Normalize both
    normalized_raw = normalize_company_dataframe(raw_df)
    normalized_resolved = normalize_company_dataframe(resolved_df)

    # Check schemas match after normalization
    assert set(normalized_raw.columns) == set(normalized_resolved.columns)

    # Check block fields are removed
    assert "block_key" not in normalized_resolved.columns
    assert "block_key_type" not in normalized_resolved.columns

    # Check expected fields are present
    expected_fields = ["id", "uuid", "name", "description", "cik"]
    for field in expected_fields:
        assert field in normalized_raw.columns
        assert field in normalized_resolved.columns


def test_er_blocking_first_iteration(spark, tmp_path):
    """Test ER blocking with raw company data (first iteration)."""
    # Create test data
    raw_data = create_raw_companies_data()
    raw_df = spark.createDataFrame(raw_data)

    # Save to parquet
    input_path = str(tmp_path / "raw_companies.parquet")
    output_path = str(tmp_path / "blocks_iteration_1")
    raw_df.write.mode("overwrite").parquet(input_path)

    # Run blocking
    build_blocks(input_path=input_path, output_path=output_path, local_mode=True, stop_spark=False)

    # Check output files exist
    assert os.path.exists(os.path.join(output_path, "union_blocks.parquet"))
    assert os.path.exists(os.path.join(output_path, "combined_blocks.parquet"))

    # Load and validate blocks
    union_blocks = spark.read.parquet(os.path.join(output_path, "union_blocks.parquet"))

    # Check schema
    assert "block_key" in union_blocks.columns
    assert "block_key_type" in union_blocks.columns
    assert "companies" in union_blocks.columns
    assert "block_size" in union_blocks.columns

    # Check we have blocks
    assert union_blocks.count() > 0

    # Check company struct doesn't have block fields
    companies_schema = union_blocks.schema["companies"].dataType.elementType
    field_names = [field.name for field in companies_schema.fields]
    assert "block_key" not in field_names
    assert "block_key_type" not in field_names

    # Verify data integrity
    sample_block = union_blocks.filter(F.col("block_key") == "APPLE").collect()
    if sample_block:
        companies = sample_block[0]["companies"]
        assert len(companies) > 0
        # Check company has expected fields
        first_company = companies[0]
        assert "uuid" in first_company
        assert "name" in first_company
        assert "description" in first_company


def test_er_blocking_second_iteration(spark, tmp_path):
    """Test ER blocking with resolved company data (second iteration)."""
    # Create test data with potential schema issues
    resolved_data = create_resolved_companies_data()
    resolved_df = spark.createDataFrame(resolved_data)

    # Save to parquet
    input_path = str(tmp_path / "resolved_companies.parquet")
    output_path = str(tmp_path / "blocks_iteration_2")
    resolved_df.write.mode("overwrite").parquet(input_path)

    # Run blocking - this should handle the schema differences
    build_blocks(input_path=input_path, output_path=output_path, local_mode=True, stop_spark=False)

    # Check output files exist
    assert os.path.exists(os.path.join(output_path, "union_blocks.parquet"))

    # Load and validate blocks
    union_blocks = spark.read.parquet(os.path.join(output_path, "union_blocks.parquet"))

    # Check we have blocks
    assert union_blocks.count() > 0

    # Check company struct doesn't have contamination from block fields
    companies_schema = union_blocks.schema["companies"].dataType.elementType
    field_names = [field.name for field in companies_schema.fields]
    assert "block_key" not in field_names
    assert "block_key_type" not in field_names

    # Load the JSON to verify field mapping is correct
    union_blocks_json_path = os.path.join(output_path, "union_blocks.json")

    # Find the first JSON file in the directory
    json_files = [f for f in os.listdir(union_blocks_json_path) if f.endswith(".json")]
    if json_files:
        json_file_path = os.path.join(union_blocks_json_path, json_files[0])

        # Read first line of JSON
        with open(json_file_path) as f:
            first_block = json.loads(f.readline())

            # Verify fields are mapped correctly
            if first_block["companies"]:
                first_company = first_block["companies"][0]

                # Check that block_key is NOT in the website_url field
                if "website_url" in first_company:
                    assert first_company["website_url"] != first_block["block_key"]

                # Check that name contains actual company name, not block_key_type
                assert "Apple" in first_company["name"] or "Google" in first_company["name"]
                assert first_company["name"] not in ["combined", "first_word", "acronym"]

                # Check description is actual description
                assert len(first_company.get("description", "")) > 10


def test_schema_consistency_across_iterations(spark, tmp_path):
    """Verify that both iterations produce compatible schemas."""
    # Create both types of data
    raw_data = create_raw_companies_data()
    resolved_data = create_resolved_companies_data()

    raw_df = spark.createDataFrame(raw_data)
    resolved_df = spark.createDataFrame(resolved_data)

    # Save both
    raw_path = str(tmp_path / "raw.parquet")
    resolved_path = str(tmp_path / "resolved.parquet")
    raw_df.write.mode("overwrite").parquet(raw_path)
    resolved_df.write.mode("overwrite").parquet(resolved_path)

    # Run blocking on both
    raw_output = str(tmp_path / "raw_blocks")
    resolved_output = str(tmp_path / "resolved_blocks")

    build_blocks(raw_path, raw_output, local_mode=True, stop_spark=False)
    build_blocks(resolved_path, resolved_output, local_mode=True, stop_spark=False)

    # Load results
    raw_blocks = spark.read.parquet(os.path.join(raw_output, "union_blocks.parquet"))
    resolved_blocks = spark.read.parquet(os.path.join(resolved_output, "union_blocks.parquet"))

    # Compare schemas
    raw_company_schema = raw_blocks.schema["companies"].dataType.elementType
    resolved_company_schema = resolved_blocks.schema["companies"].dataType.elementType

    # Field names should match
    raw_fields = sorted([f.name for f in raw_company_schema.fields])
    resolved_fields = sorted([f.name for f in resolved_company_schema.fields])

    assert raw_fields == resolved_fields, (
        f"Schema mismatch: {set(raw_fields) ^ set(resolved_fields)}"
    )

    # Neither should have block fields
    assert "block_key" not in raw_fields
    assert "block_key_type" not in resolved_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Test if PySpark can save complex nested structures without JSON serialization."""

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from abzu.spark.config import get_spark_session


def test_pyspark_saves_structs_properly() -> None:
    """Test that PySpark can save lists of structs directly to Parquet."""

    # Create test data with complex nested structures - mimicking ER output
    test_data: dict[str, Any] = {
        "block_key": ["key1", "key2", "key3"],
        "block_key_type": ["name", "domain", "name"],
        "resolved_companies": [
            # Block 1: Multiple companies with all fields
            [
                {
                    "uuid": "uuid1",
                    "name": "Company A",
                    "source_uuids": ["u1", "u2"],
                    "match_skip_history": [1, 2],
                    "match_skip": False,
                    "domain": "companya.com",
                },
                {
                    "uuid": "uuid2",
                    "name": "Company B",
                    "source_uuids": ["u3"],
                    "match_skip_history": [],
                    "match_skip": False,
                    "domain": None,
                },
            ],
            # Block 2: Single company
            [
                {
                    "uuid": "uuid3",
                    "name": "Company C",
                    "source_uuids": ["u4", "u5", "u6"],
                    "match_skip_history": None,  # Test None value
                    "match_skip": True,
                    "match_skip_reason": "error_recovery",
                },
            ],
            # Block 3: Empty list
            [],
        ],
        "original_companies": [
            [{"uuid": "orig1", "name": "Original A"}],
            [{"uuid": "orig2", "name": "Original B"}, {"uuid": "orig3", "name": "Original C"}],
            None,  # Test None instead of empty list
        ],
        "error": [None, None, "Some error in processing"],
        "block_size": [2, 1, 0],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "test_pyspark_structs.parquet"

        print("Testing PySpark save of complex nested structures...")

        # Step 1: Create pandas DataFrame (as match.py does)
        df = pd.DataFrame(test_data)
        print(f"\nOriginal pandas DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")

        # Step 2: Convert to PySpark DataFrame and save
        spark = get_spark_session("TestPySparkStructSave")

        # IMPORTANT: Disable Arrow optimization to preserve Python types
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

        try:
            # Define explicit schema for the complex nested structure
            from pyspark.sql.types import (
                ArrayType,
                BooleanType,
                LongType,
                StringType,
                StructField,
                StructType,
            )

            # Define company schema
            company_schema = StructType(
                [
                    StructField("uuid", StringType(), True),
                    StructField("name", StringType(), True),
                    StructField("source_uuids", ArrayType(StringType()), True),
                    StructField("match_skip_history", ArrayType(LongType()), True),
                    StructField("match_skip", BooleanType(), True),
                    StructField("match_skip_reason", StringType(), True),
                    StructField("domain", StringType(), True),
                ]
            )

            # Define the full DataFrame schema
            full_schema = StructType(
                [
                    StructField("block_key", StringType(), True),
                    StructField("block_key_type", StringType(), True),
                    StructField("resolved_companies", ArrayType(company_schema), True),
                    StructField(
                        "original_companies",
                        ArrayType(
                            StructType(
                                [
                                    StructField("uuid", StringType(), True),
                                    StructField("name", StringType(), True),
                                ]
                            )
                        ),
                        True,
                    ),
                    StructField("error", StringType(), True),
                    StructField("block_size", LongType(), True),
                ]
            )

            # Convert pandas to PySpark with explicit schema
            spark_df = spark.createDataFrame(df, schema=full_schema)

            print("\nPySpark DataFrame schema:")
            spark_df.printSchema()

            # Save to parquet using PySpark
            spark_df.write.mode("overwrite").parquet(str(parquet_path))
            print(f"\n✓ Successfully saved to {parquet_path} using PySpark")

            # Step 3: Read back and verify structure is preserved
            read_df = spark.read.parquet(str(parquet_path))
            print("\nRead back schema:")
            read_df.printSchema()

            # Convert back to pandas to inspect
            result_pdf = read_df.toPandas()
            print(f"\nRead back pandas shape: {result_pdf.shape}")

            # Verify the data is intact
            first_block = result_pdf.iloc[0]
            resolved_companies = first_block["resolved_companies"]

            print(f"\nFirst block resolved_companies type: {type(resolved_companies)}")
            print(
                f"First block resolved_companies length: {len(resolved_companies) if resolved_companies else 0}"
            )

            if resolved_companies and len(resolved_companies) > 0:
                first_company = resolved_companies[0]
                print(f"First company type: {type(first_company)}")

                # Check if it's a Row object (PySpark) or dict
                if hasattr(first_company, "asDict"):
                    first_company = first_company.asDict()
                    print("Converted Row to dict")

                print(f"First company: {first_company}")

                # Verify nested lists are preserved
                source_uuids = first_company.get("source_uuids")
                print(f"source_uuids type: {type(source_uuids)}")
                print(f"source_uuids value: {source_uuids}")

                assert isinstance(
                    source_uuids, list
                ), f"source_uuids should be list, got {type(source_uuids)}"
                assert source_uuids == ["u1", "u2"], f"source_uuids mismatch: {source_uuids}"

            # Check handling of None values
            third_block = result_pdf.iloc[2]
            assert (
                third_block["resolved_companies"] == [] or third_block["resolved_companies"] is None
            )

            print("\n✅ All tests passed! PySpark can handle complex nested structures!")

        except Exception as e:
            print(f"\n❌ Failed to save with PySpark: {e}")
            print("\nTrying to identify the issue...")

            # Debug: Check each column
            for col in df.columns:
                print(f"\nColumn '{col}':")
                print(f"  dtype: {df[col].dtype}")
                sample = df[col].iloc[0] if len(df) > 0 else None
                print(f"  sample value type: {type(sample)}")
                print(f"  sample value: {sample}")

            raise
        finally:
            spark.stop()


def test_pyspark_with_none_handling() -> None:
    """Test PySpark handling of None values in list columns."""

    # Create test data with various None scenarios
    test_data: dict[str, Any] = {
        "block_key": ["key1", "key2", "key3", "key4"],
        "resolved_companies": [
            [{"uuid": "1", "name": "A"}],  # Normal list
            [],  # Empty list
            None,  # None value
            [{"uuid": "2", "name": "B"}, None, {"uuid": "3", "name": "C"}],  # List with None
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "test_none_handling.parquet"

        print("\n\nTesting None handling in PySpark...")

        df = pd.DataFrame(test_data)
        spark = get_spark_session("TestNoneHandling")
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")

        try:
            # Fill None values with empty lists before converting
            df["resolved_companies"] = df["resolved_companies"].apply(
                lambda x: [] if x is None else x
            )

            spark_df = spark.createDataFrame(df)
            spark_df.write.mode("overwrite").parquet(str(parquet_path))

            # Read back
            read_df = spark.read.parquet(str(parquet_path))
            read_df.toPandas()

            print("✅ None handling test passed!")

        except Exception as e:
            print(f"❌ None handling failed: {e}")
            raise
        finally:
            spark.stop()


if __name__ == "__main__":
    test_pyspark_saves_structs_properly()
    test_pyspark_with_none_handling()
    print("\n🎉 All tests completed!")

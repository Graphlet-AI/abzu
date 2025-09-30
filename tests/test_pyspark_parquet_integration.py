"""Test the PySpark parquet integration for ER pipeline."""

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from abzu.spark.config import get_spark_session
from abzu.spark.pandas_to_parquet import save_pandas_df_with_pyspark


def test_er_pipeline_with_pyspark_parquet() -> None:
    """Test that the ER pipeline can save and load complex data using PySpark."""

    # Create test data mimicking ER match output
    test_data: dict[str, Any] = {
        "block_key": ["key1", "key2", "key3"],
        "block_key_type": ["name", "domain", "name"],
        "resolved_companies": [
            # Block 1: Multiple companies
            [
                {
                    "uuid": "uuid1",
                    "name": "Company A",
                    "source_uuids": ["u1", "u2"],
                    "match_skip_history": [1, 2],
                    "match_skip": False,
                    "match_skip_reason": None,
                    "domain": "companya.com",
                    "ticker": {"symbol": "CMPA", "exchange": "NASDAQ"},
                    "aliases": ["CompA", "Company Alpha"],
                    "categories": ["tech", "software"],
                },
                {
                    "uuid": "uuid2",
                    "name": "Company B",
                    "source_uuids": ["u3"],
                    "match_skip_history": [],
                    "match_skip": False,
                    "match_skip_reason": None,
                    "domain": None,
                    "ticker": None,
                    "aliases": [],
                    "categories": None,
                },
            ],
            # Block 2: Single company with error recovery
            [
                {
                    "uuid": "uuid3",
                    "name": "Company C",
                    "source_uuids": ["u4", "u5", "u6"],
                    "match_skip_history": [1],
                    "match_skip": True,
                    "match_skip_reason": "error_recovery",
                    "domain": "companyc.com",
                    "ticker": None,
                    "aliases": None,
                    "categories": ["finance"],
                },
            ],
            # Block 3: Empty (no matches)
            [],
        ],
        "original_companies": [
            [{"uuid": "orig1", "name": "Original A"}],
            [{"uuid": "orig2", "name": "Original B"}],
            None,  # Will be converted to empty list
        ],
        "error": [None, None, "Some processing error"],
        "block_size": [2, 1, 0],
        "processing_time": ["1.23s", "0.45s", "0.12s"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = str(Path(tmpdir) / "test_matches_iteration_1.parquet")

        print("Testing PySpark parquet integration for ER pipeline...")

        # Step 1: Create pandas DataFrame (as match.py does)
        df = pd.DataFrame(test_data)
        print("\n1. Original pandas DataFrame:")
        print(f"   Shape: {df.shape}")
        print(f"   resolved_companies[0] type: {type(df['resolved_companies'].iloc[0])}")

        # Step 2: Save using PySpark (as updated match.py does)
        from pyspark.sql.types import (
            ArrayType,
            BooleanType,
            LongType,
            StringType,
            StructField,
            StructType,
        )

        # Define the schema
        company_schema = StructType(
            [
                StructField("uuid", StringType(), True),
                StructField("name", StringType(), True),
                StructField("source_uuids", ArrayType(StringType()), True),
                StructField("match_skip_history", ArrayType(LongType()), True),
                StructField("match_skip", BooleanType(), True),
                StructField("match_skip_reason", StringType(), True),
                StructField("domain", StringType(), True),
                StructField(
                    "ticker",
                    StructType(
                        [
                            StructField("symbol", StringType(), True),
                            StructField("exchange", StringType(), True),
                        ]
                    ),
                    True,
                ),
                StructField("aliases", ArrayType(StringType()), True),
                StructField("categories", ArrayType(StringType()), True),
            ]
        )

        results_schema = StructType(
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
                StructField("processing_time", StringType(), True),
            ]
        )

        save_pandas_df_with_pyspark(
            df, parquet_path, schema=results_schema, app_name="TestERPipeline"
        )
        print(f"\n2. ✓ Saved with PySpark to {parquet_path}")

        # Step 3: Load with PySpark (as er_eval.py does)
        spark = get_spark_session("TestERPipelineRead")
        spark_df = spark.read.parquet(parquet_path)

        print("\n3. Loaded with PySpark:")
        print("   Schema:")
        spark_df.printSchema()

        # Step 4: Test that we can explode and work with the data
        from pyspark.sql import functions as F

        exploded_df = spark_df.select(
            "block_key", F.explode("resolved_companies").alias("company")
        ).select(
            "block_key",
            F.col("company.uuid").alias("uuid"),
            F.col("company.name").alias("name"),
            F.col("company.source_uuids").alias("source_uuids"),
            F.col("company.match_skip").alias("match_skip"),
        )

        results = exploded_df.collect()
        print(f"\n4. ✓ Successfully exploded {len(results)} companies")

        # Step 5: Verify data integrity
        first_company = results[0]
        assert first_company["uuid"] == "uuid1"
        assert first_company["name"] == "Company A"
        assert first_company["source_uuids"] == ["u1", "u2"]
        assert first_company["match_skip"] == False
        print("\n5. ✓ Data integrity verified")

        # Step 6: Test loading back to pandas (preserving lists)
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
        pdf_back = spark_df.toPandas()

        first_block = pdf_back.iloc[0]
        resolved = first_block["resolved_companies"]
        assert isinstance(resolved, list), f"Expected list, got {type(resolved)}"
        print("\n6. ✓ Pandas conversion preserves lists")

        # Check that nested lists are preserved
        if len(resolved) > 0:
            first_company_back = resolved[0]
            # Convert Row to dict if needed
            if hasattr(first_company_back, "asDict"):
                first_company_back = first_company_back.asDict()

            source_uuids = first_company_back.get("source_uuids")
            assert isinstance(
                source_uuids, list
            ), f"source_uuids should be list, got {type(source_uuids)}"
            assert source_uuids == ["u1", "u2"]
            print(f"   ✓ Nested lists preserved: {source_uuids}")

        spark.stop()
        print("\n✅ All tests passed! PySpark parquet integration works correctly!")


if __name__ == "__main__":
    test_er_pipeline_with_pyspark_parquet()

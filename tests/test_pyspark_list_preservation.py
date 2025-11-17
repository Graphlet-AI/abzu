"""Test that PySpark preserves Python lists when loading parquet files."""

import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from abzu.spark.config import get_spark_session


def test_pyspark_preserves_lists() -> None:
    """Test that PySpark preserves Python lists when loading parquet files."""
    # Create test data with lists
    test_data = {
        "id": [1, 2, 3],
        "name": ["Company A", "Company B", "Company C"],
        "source_uuids": [
            ["uuid1", "uuid2"],
            ["uuid3"],
            ["uuid4", "uuid5", "uuid6"],
        ],
        "match_skip_history": [
            [1, 2],
            [1],
            [2, 3, 4],
        ],
    }

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "test.parquet"

        # Save with pandas
        df = pd.DataFrame(test_data)
        df.to_parquet(parquet_path)

        # Load with pandas (default) - this creates numpy arrays
        pandas_df = pd.read_parquet(parquet_path)
        assert hasattr(
            pandas_df["source_uuids"].iloc[0], "tolist"
        ), "Pandas default converts lists to numpy arrays"

        # Load with PySpark
        spark = get_spark_session("TestListPreservation")
        # Disable Arrow optimization to preserve Python object types
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
        spark_df = spark.read.parquet(str(parquet_path))
        pyspark_df = spark_df.toPandas()

        # Verify lists are preserved
        for i in range(len(test_data["id"])):
            # Check source_uuids
            source_uuids = pyspark_df["source_uuids"].iloc[i]
            assert isinstance(
                source_uuids, list
            ), f"source_uuids should be list, got {type(source_uuids)}"
            assert source_uuids == test_data["source_uuids"][i]

            # Check match_skip_history
            skip_history = pyspark_df["match_skip_history"].iloc[i]
            assert isinstance(
                skip_history, list
            ), f"match_skip_history should be list, got {type(skip_history)}"
            assert skip_history == test_data["match_skip_history"][i]

        spark.stop()


def test_pyspark_with_nested_structs() -> None:
    """Test PySpark with nested struct data like companies."""
    test_data: dict[str, list[Any]] = {
        "block_key": ["key1", "key2"],
        "block_key_type": ["name", "domain"],
        "companies": [
            [
                {
                    "uuid": "uuid1",
                    "name": "Company A",
                    "source_uuids": ["uuid1"],
                    "match_skip_history": [1],
                },
                {
                    "uuid": "uuid2",
                    "name": "Company B",
                    "source_uuids": ["uuid2"],
                    "match_skip_history": [],
                },
            ],
            [
                {
                    "uuid": "uuid3",
                    "name": "Company C",
                    "source_uuids": ["uuid3", "uuid4"],
                    "match_skip_history": [1, 2],
                }
            ],
        ],
        "block_size": [2, 1],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "blocks.parquet"

        # Save with pandas
        df = pd.DataFrame(test_data)
        df.to_parquet(parquet_path)

        # Load with PySpark
        spark = get_spark_session("TestNestedStructs")
        # Disable Arrow optimization to preserve Python object types
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
        spark_df = spark.read.parquet(str(parquet_path))
        pyspark_df = spark_df.toPandas()

        # Verify nested lists are preserved
        for i in range(len(test_data["block_key"])):
            companies = pyspark_df["companies"].iloc[i]
            assert isinstance(companies, list), f"companies should be list, got {type(companies)}"

            for j, company in enumerate(companies):
                # Each company should be a dict or Row (PySpark's representation)
                from pyspark.sql.types import Row

                assert isinstance(
                    company, (dict, Row)
                ), f"company should be dict or Row, got {type(company)}"

                # Check nested lists within company (Row objects support attribute access)
                if isinstance(company, Row):
                    source_uuids = company.source_uuids
                    skip_history = company.match_skip_history
                else:
                    source_uuids = company.get("source_uuids")
                    skip_history = company.get("match_skip_history")

                assert isinstance(
                    source_uuids, list
                ), f"company source_uuids should be list, got {type(source_uuids)}"

                assert isinstance(
                    skip_history, list
                ), f"company match_skip_history should be list, got {type(skip_history)}"

        spark.stop()


def test_compare_loading_methods() -> None:
    """Compare different parquet loading methods and their handling of lists."""
    test_data: dict[str, list[list[str] | list[int]]] = {
        "id": [1],
        "list_field": [["a", "b", "c"]],
        "int_list": [[1, 2, 3]],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "compare.parquet"

        # Save with pandas
        df = pd.DataFrame(test_data)
        df.to_parquet(parquet_path)

        # Method 1: pandas default (creates numpy arrays)
        pandas_default = pd.read_parquet(parquet_path)
        assert hasattr(
            pandas_default["list_field"].iloc[0], "tolist"
        ), "Default pandas creates numpy arrays"

        # Method 2: PySpark (preserves Python lists)
        spark = get_spark_session("TestComparison")
        # Disable Arrow optimization to preserve Python object types
        spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
        spark_df = spark.read.parquet(str(parquet_path))
        pyspark_result = spark_df.toPandas()

        assert isinstance(
            pyspark_result["list_field"].iloc[0], list
        ), "PySpark should preserve Python lists"
        assert isinstance(
            pyspark_result["int_list"].iloc[0], list
        ), "PySpark should preserve integer lists"

        spark.stop()


if __name__ == "__main__":
    test_pyspark_preserves_lists()
    test_pyspark_with_nested_structs()
    test_compare_loading_methods()
    print("All tests passed!")

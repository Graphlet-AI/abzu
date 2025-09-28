"""Test that parquet loading preserves Python lists instead of converting to numpy arrays."""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def test_parquet_with_pyarrow_backend(tmp_path: Path) -> None:
    """Test that dtype_backend='pyarrow' preserves Python lists."""

    # Create test data with lists
    test_data: dict[str, Any] = {
        "block_key": ["KEY1", "KEY2"],
        "block_key_type": ["name", "name"],
        "block_size": [2, 1],
        "companies": [
            [
                {
                    "id": 1,
                    "uuid": "uuid-1",
                    "name": "Company A",
                    "description": "Test company A",
                    "source_uuids": ["uuid-a", "uuid-b"],
                    "source_ids": [100, 101],
                    "match_skip_history": [1],
                },
                {
                    "id": 2,
                    "uuid": "uuid-2",
                    "name": "Company B",
                    "description": "Test company B",
                    "source_uuids": ["uuid-c"],
                    "source_ids": [102],
                    "match_skip_history": None,
                },
            ],
            [
                {
                    "id": 3,
                    "uuid": "uuid-3",
                    "name": "Company C",
                    "description": "Test company C",
                    "source_uuids": [],
                    "source_ids": [],
                    "match_skip_history": [],
                }
            ],
        ],
    }

    df = pd.DataFrame(test_data)

    # Save to parquet
    parquet_path = tmp_path / "test_blocks.parquet"
    df.to_parquet(parquet_path, index=False)

    # Load back with dtype_backend='pyarrow' to preserve lists
    df_loaded = pd.read_parquet(parquet_path, dtype_backend="pyarrow")

    # Check that lists are preserved as Python lists, NOT numpy arrays
    for companies in df_loaded["companies"]:
        assert isinstance(companies, list), "companies should be a list with pyarrow backend"
        assert not isinstance(companies, np.ndarray), "companies should NOT be a numpy array"
        for company in companies:
            if "source_uuids" in company and company["source_uuids"] is not None:
                assert isinstance(company["source_uuids"], list), "source_uuids should be a list"
                # Test that we can append to it (would fail with numpy array)
                test_uuid = "test-uuid"
                company["source_uuids"].append(test_uuid)
                assert test_uuid in company["source_uuids"], "Should be able to append to list"

            if "source_ids" in company and company["source_ids"] is not None:
                assert isinstance(company["source_ids"], list), "source_ids should be a list"
                # Test that we can append to it
                test_id = 999
                company["source_ids"].append(test_id)
                assert test_id in company["source_ids"], "Should be able to append to list"

            if "match_skip_history" in company and company["match_skip_history"] is not None:
                assert isinstance(
                    company["match_skip_history"], list
                ), "match_skip_history should be a list"
                # Test that we can append to it
                test_iteration = 2
                company["match_skip_history"].append(test_iteration)
                assert (
                    test_iteration in company["match_skip_history"]
                ), "Should be able to append to list"


def test_parquet_without_pyarrow_creates_arrays(tmp_path: Path) -> None:
    """Test documenting that without dtype_backend='pyarrow', pandas converts lists to numpy arrays."""

    # Create test data with lists
    test_data: dict[str, Any] = {
        "list_column": [[1, 2, 3], [4, 5], [6]],
        "string_list": [["a", "b"], ["c"], ["d", "e", "f"]],
    }

    df = pd.DataFrame(test_data)

    # Save to parquet
    parquet_path = tmp_path / "test_arrays.parquet"
    df.to_parquet(parquet_path, index=False)

    # Load back - pandas/pyarrow will convert lists to numpy arrays
    df_loaded = pd.read_parquet(parquet_path)

    # This creates numpy arrays, not Python lists
    first_val = df_loaded["list_column"].iloc[0]
    # Document the problem - lists become numpy arrays
    assert isinstance(first_val, np.ndarray), "Parquet loading converts lists to numpy arrays"

    # But with dtype_backend='pyarrow', lists are preserved
    df_loaded_pyarrow = pd.read_parquet(parquet_path, dtype_backend="pyarrow")
    first_val_pyarrow = df_loaded_pyarrow["list_column"].iloc[0]
    # This preserves Python lists!
    assert isinstance(first_val_pyarrow, list), "dtype_backend='pyarrow' preserves Python lists"
    assert not isinstance(
        first_val_pyarrow, np.ndarray
    ), "dtype_backend='pyarrow' prevents numpy arrays"


def test_match_entities_preserves_lists(tmp_path: Path) -> None:
    """Test that match_entities preserves lists when loading parquet data."""
    # Create mock blocks data with lists
    test_data = {
        "block_key": ["KEY1"],
        "block_key_type": ["name"],
        "block_size": [2],
        "companies": [
            [
                {
                    "id": 1,
                    "uuid": "uuid-1",
                    "name": "Test Company",
                    "description": "A test company",
                    "match_skip": True,
                    "match_skip_reason": "singleton_block",
                    "match_skip_history": [1],  # This must remain a list
                    "source_uuids": ["uuid-1"],  # This must remain a list
                    "source_ids": [1],  # This must remain a list
                }
            ]
        ],
    }

    df = pd.DataFrame(test_data)

    # Save as blocks
    blocks_path = str(tmp_path / "blocks_iter_{iteration}.{format}")
    blocks_parquet = blocks_path.format(iteration=1, format="parquet")
    df.to_parquet(blocks_parquet, index=False)

    # Load with pyarrow backend (as match.py does)
    df_loaded = pd.read_parquet(blocks_parquet, dtype_backend="pyarrow")

    # Verify all lists are preserved as Python lists
    companies = df_loaded["companies"].iloc[0]
    assert isinstance(companies, list), "Companies should be a Python list"
    assert not isinstance(companies, np.ndarray), "Companies should NOT be a numpy array"

    for company in companies:
        # Check that all list fields are Python lists
        if "match_skip_history" in company and company["match_skip_history"] is not None:
            assert isinstance(
                company["match_skip_history"], list
            ), "match_skip_history should be a list"
            assert not isinstance(
                company["match_skip_history"], np.ndarray
            ), "match_skip_history should NOT be numpy array"
            # Test that we can append (would fail with numpy array)
            company["match_skip_history"].append(2)
            assert 2 in company["match_skip_history"], "Should be able to append to list"

        if "source_uuids" in company and company["source_uuids"] is not None:
            assert isinstance(company["source_uuids"], list), "source_uuids should be a list"
            assert not isinstance(
                company["source_uuids"], np.ndarray
            ), "source_uuids should NOT be numpy array"

        if "source_ids" in company and company["source_ids"] is not None:
            assert isinstance(company["source_ids"], list), "source_ids should be a list"
            assert not isinstance(
                company["source_ids"], np.ndarray
            ), "source_ids should NOT be numpy array"

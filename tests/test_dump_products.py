"""Tests for the dump_products_main function."""

import io
import os
from unittest import mock

import pandas as pd

from abzu.dump.products import dump_products_main


def test_dump_products_main_old_schema(tmp_path):
    """Test the dump_products_main function with the old schema."""
    # Create a test DataFrame with the old schema
    df = pd.DataFrame(
        {
            "company_name": ["Company A", "Company B"],
            "name": ["Product A", "Product B"],
            "description": ["Description A", "Description B"],
        }
    )

    # Save the DataFrame to a parquet file
    test_file = os.path.join(tmp_path, "test_products.parquet")
    df.to_parquet(test_file)

    # Capture stdout to verify output
    with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        result = dump_products_main(test_file)

    # Check the result
    assert result == 0
    output = fake_stdout.getvalue()
    assert "Company A" in output
    assert "Product A" in output
    assert "Description A" in output
    assert "Company B" in output
    assert "Product B" in output
    assert "Description B" in output


def test_dump_products_main_new_schema(tmp_path):
    """Test the dump_products_main function with the new schema."""
    # Create a test DataFrame with the new schema
    df = pd.DataFrame(
        {
            "manufacturer_name": ["Company A", "Company B"],
            "name": ["Product A", "Product B"],
            "description": ["Description A", "Description B"],
        }
    )

    # Save the DataFrame to a parquet file
    test_file = os.path.join(tmp_path, "test_products_new.parquet")
    df.to_parquet(test_file)

    # Capture stdout to verify output
    with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        result = dump_products_main(test_file)

    # Check the result
    assert result == 0
    output = fake_stdout.getvalue()
    assert "Company A" in output
    assert "Product A" in output
    assert "Description A" in output
    assert "Company B" in output
    assert "Product B" in output
    assert "Description B" in output


def test_dump_products_main_missing_columns(tmp_path):
    """Test the dump_products_main function with missing columns."""
    # Create a test DataFrame with missing required columns
    df = pd.DataFrame(
        {
            "manufacturer_name": ["Company A", "Company B"],
            # Missing "name" column
            "description": ["Description A", "Description B"],
        }
    )

    # Save the DataFrame to a parquet file
    test_file = os.path.join(tmp_path, "test_products_missing.parquet")
    df.to_parquet(test_file)

    # Should log an error and return 1
    with mock.patch("abzu.dump.products.logger.error") as mock_error:
        result = dump_products_main(test_file)

    # Check the result
    assert result == 1
    mock_error.assert_called_once()
    assert "Missing required columns" in mock_error.call_args[0][0]


def test_dump_products_main_file_not_found():
    """Test the dump_products_main function with a non-existent file."""
    # Should log an error and return 1
    with mock.patch("abzu.dump.products.logger.error") as mock_error:
        result = dump_products_main("non_existent_file.parquet")

    # Check the result
    assert result == 1
    mock_error.assert_called_once()
    assert "Failed to read products file" in mock_error.call_args[0][0]


def test_dump_products_main_no_sort_column(tmp_path):
    """Test the dump_products_main function with no sort column."""
    # Create a test DataFrame with neither company_name nor manufacturer_name
    df = pd.DataFrame(
        {
            "name": ["Product A", "Product B"],
            "description": ["Description A", "Description B"],
        }
    )

    # Save the DataFrame to a parquet file
    test_file = os.path.join(tmp_path, "test_products_no_sort.parquet")
    df.to_parquet(test_file)

    # Capture stdout to verify output
    with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
        result = dump_products_main(test_file)

    # Check the result
    assert result == 0
    output = fake_stdout.getvalue()
    assert "Product A" in output
    assert "Description A" in output
    assert "Product B" in output
    assert "Description B" in output

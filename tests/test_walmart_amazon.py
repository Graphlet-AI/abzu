"""Tests for the walmart_amazon download CLI command."""

import zipfile
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests
from click.testing import CliRunner

from abzu.cli.download.walmart_amazon import walmart_amazon


@pytest.fixture
def mock_csv_data():
    """Create mock CSV data for testing."""
    return pd.DataFrame(
        {
            "walmart_id": ["W1", "W2", "W3"],
            "amazon_id": ["A1", "A2", "A3"],
            "product_name": ["Product 1", "Product 2", "Product 3"],
            "match_score": [0.95, 0.87, 0.92],
        }
    )


@pytest.fixture
def create_zip_with_csv(tmp_path, mock_csv_data):
    """Create a ZIP file containing CSV files for testing."""

    def _create_zip(num_files=1):
        zip_path = tmp_path / "test_data.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(num_files):
                csv_content = mock_csv_data.to_csv(index=False)
                zf.writestr(f"data_{i}.csv", csv_content)
        return zip_path

    return _create_zip


def test_walmart_amazon_help():
    """Test the help command for walmart_amazon."""
    runner = CliRunner()
    result = runner.invoke(walmart_amazon, ["--help"])
    assert result.exit_code == 0
    assert "Download and convert Walmart-Amazon dataset" in result.output
    assert "--output-dir" in result.output
    assert "--force" in result.output


def test_walmart_amazon_url_handling(tmp_path):
    """Test that the command uses the correct URL."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        # Mock the response
        mock_response = Mock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.iter_content = lambda chunk_size: [b"data"]
        mock_get.return_value = mock_response

        # Mock zipfile to avoid actual extraction
        with patch("abzu.cli.download.walmart_amazon.zipfile.ZipFile"):
            runner.invoke(walmart_amazon, ["-o", str(output_dir)])

        # Verify the correct URL was called
        expected_url = "https://zenodo.org/records/8164151/files/Dn4.zip?download=1"
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == expected_url


def test_walmart_amazon_successful_download(tmp_path, create_zip_with_csv):
    """Test successful download and conversion with mocked requests."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    # Create a real ZIP file with CSV data
    zip_path = create_zip_with_csv(num_files=2)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        # Mock the response to return the real ZIP file
        mock_response = Mock()
        mock_response.headers = {"content-length": str(zip_path.stat().st_size)}
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify success
    assert result.exit_code == 0
    assert "Downloading Walmart-Amazon dataset" in result.output
    assert "Converted 2/2 files to Parquet" in result.output

    # Verify Parquet files were created
    parquet_files = list(output_dir.glob("*.parquet"))
    assert len(parquet_files) == 2

    # Verify data integrity
    for parquet_file in parquet_files:
        df = pd.read_parquet(parquet_file)
        assert len(df) == 3
        assert "walmart_id" in df.columns
        assert "amazon_id" in df.columns


def test_walmart_amazon_network_failure(tmp_path):
    """Test error handling for network failures."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        # Simulate a network error
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify the command fails gracefully
    assert result.exit_code != 0
    assert "Download failed" in result.output


def test_walmart_amazon_http_error(tmp_path):
    """Test error handling for HTTP errors."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        # Simulate an HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify the command fails gracefully
    assert result.exit_code != 0


def test_walmart_amazon_zip_extraction(tmp_path, create_zip_with_csv):
    """Test ZIP extraction functionality."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    # Create a ZIP file with multiple CSV files
    zip_path = create_zip_with_csv(num_files=3)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(zip_path.stat().st_size)}
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify all CSV files were extracted and converted
    assert result.exit_code == 0
    assert "Found 3 CSV files" in result.output
    assert "Converted 3/3 files to Parquet" in result.output


def test_walmart_amazon_csv_to_parquet_conversion(tmp_path, create_zip_with_csv):
    """Test CSV to Parquet conversion."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    zip_path = create_zip_with_csv(num_files=1)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(zip_path.stat().st_size)}
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify Parquet file was created with correct data
    assert result.exit_code == 0
    parquet_files = list(output_dir.glob("*.parquet"))
    assert len(parquet_files) == 1

    # Verify the Parquet file contains the expected data
    df = pd.read_parquet(parquet_files[0])
    assert len(df) == 3
    assert list(df.columns) == ["walmart_id", "amazon_id", "product_name", "match_score"]


def test_walmart_amazon_existing_files_without_force(tmp_path):
    """Test handling of existing files without --force flag."""
    runner = CliRunner()
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy Parquet file to simulate existing files
    dummy_df = pd.DataFrame({"col1": [1, 2, 3]})
    dummy_df.to_parquet(output_dir / "existing.parquet")

    result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify the command exits early without downloading
    assert result.exit_code == 0
    assert "Found 1 Parquet files" in result.output
    assert "Use --force to re-download" in result.output
    # Should not attempt to download
    assert "Downloading Walmart-Amazon dataset" not in result.output


def test_walmart_amazon_existing_files_with_force(tmp_path, create_zip_with_csv):
    """Test --force flag to re-download existing files."""
    runner = CliRunner()
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy Parquet file to simulate existing files
    dummy_df = pd.DataFrame({"col1": [1, 2, 3]})
    existing_file = output_dir / "existing.parquet"
    dummy_df.to_parquet(existing_file)

    # Create a ZIP file with new data
    zip_path = create_zip_with_csv(num_files=1)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(zip_path.stat().st_size)}
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir), "--force"])

    # Verify the command re-downloads despite existing files
    assert result.exit_code == 0
    assert "Downloading Walmart-Amazon dataset" in result.output
    assert "Converted 1/1 files to Parquet" in result.output


def test_walmart_amazon_empty_zip(tmp_path):
    """Test handling of ZIP files with no CSV files."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    # Create an empty ZIP file
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w") as zf:
        # Add a non-CSV file
        zf.writestr("readme.txt", "This is not a CSV file")

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(empty_zip.stat().st_size)}
        with open(empty_zip, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify the command handles empty ZIP gracefully
    assert result.exit_code == 0
    assert "Found 0 CSV files" in result.output
    assert "No CSV files found in the archive" in result.output


def test_walmart_amazon_invalid_csv(tmp_path):
    """Test handling of invalid CSV files."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    # Create a ZIP file with a binary file that has .csv extension
    invalid_zip = tmp_path / "invalid.zip"
    with zipfile.ZipFile(invalid_zip, "w") as zf:
        # Add a binary file disguised as CSV - this will cause pandas to fail
        binary_data = bytes([0xFF, 0xFE, 0xFD, 0xFC] * 100)
        zf.writestr("invalid.csv", binary_data)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(invalid_zip.stat().st_size)}
        with open(invalid_zip, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify the command handles invalid CSV gracefully
    assert result.exit_code == 0
    assert "Failed to convert invalid.csv" in result.output
    assert "Converted 0/1 files to Parquet" in result.output


def test_walmart_amazon_no_content_length(tmp_path, create_zip_with_csv):
    """Test download when content-length header is missing."""
    runner = CliRunner()
    output_dir = tmp_path / "output"

    zip_path = create_zip_with_csv(num_files=1)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        # Mock response without content-length header
        mock_response = Mock()
        mock_response.headers = {}  # No content-length
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify download works without content-length
    assert result.exit_code == 0
    assert "Converted 1/1 files to Parquet" in result.output


def test_walmart_amazon_creates_output_directory(tmp_path):
    """Test that output directory is created if it doesn't exist."""
    runner = CliRunner()
    output_dir = tmp_path / "new_directory" / "nested"

    # Verify directory doesn't exist
    assert not output_dir.exists()

    # Create a ZIP file
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        csv_content = "col1,col2\n1,2\n"
        zf.writestr("data.csv", csv_content)

    with patch("abzu.cli.download.walmart_amazon.requests.get") as mock_get:
        mock_response = Mock()
        mock_response.headers = {"content-length": str(zip_path.stat().st_size)}
        with open(zip_path, "rb") as f:
            zip_content = f.read()
        mock_response.iter_content = lambda chunk_size: [zip_content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = runner.invoke(walmart_amazon, ["-o", str(output_dir)])

    # Verify directory was created
    assert result.exit_code == 0
    assert output_dir.exists()
    assert output_dir.is_dir()

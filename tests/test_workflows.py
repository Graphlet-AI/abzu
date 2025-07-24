"""Tests for workflow implementations."""

from unittest.mock import Mock, patch

import pytest

from abzu.workflows.cache_workflow import cache_sync_workflow


@pytest.fixture
def mock_state_store():
    """Create a mock state store."""
    with patch("abzu.workflows.cache_workflow.DaprStateStore") as mock:
        store = Mock()
        mock.return_value = store
        yield store


@pytest.fixture
def mock_s3_storage():
    """Create a mock S3 storage."""
    with patch("abzu.workflows.cache_workflow.DaprS3Storage") as mock:
        storage = Mock()
        mock.return_value = storage
        yield storage


@pytest.fixture
def cache_workflow(mock_state_store, mock_s3_storage):
    """Create a cache_sync_workflow instance with mocked dependencies."""
    return cache_sync_workflow()


class Testcache_sync_workflow:
    """Test suite for cache_sync_workflow class."""

    def test_init(self, mock_state_store, mock_s3_storage):
        """Test cache_sync_workflow initialization."""
        workflow = cache_sync_workflow()
        assert workflow.state_store == mock_state_store
        assert workflow.s3_storage == mock_s3_storage

    def test_check_cloud_cache_success(self, cache_workflow, mock_s3_storage):
        """Test successful cloud cache check."""
        mock_s3_storage.list.return_value = ["file1.txt", "file2.txt"]
        result = cache_workflow.check_cloud_cache("prefix/")
        assert result["success"] is True
        assert result["data"] == ["file1.txt", "file2.txt"]
        mock_s3_storage.list.assert_called_once_with("prefix/")

    def test_check_cloud_cache_error(self, cache_workflow, mock_s3_storage):
        """Test cloud cache check with error."""
        mock_s3_storage.list.side_effect = Exception("Test error")
        result = cache_workflow.check_cloud_cache("prefix/")
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_download_from_cloud_success(self, cache_workflow, mock_s3_storage, mock_state_store):
        """Test successful download from cloud."""
        mock_s3_storage.download.return_value = b"test content"
        mock_state_store.set.return_value = True

        result = cache_workflow.download_from_cloud("test.txt")
        assert result["success"] is True
        assert result["data"] == "test.txt"

        mock_s3_storage.download.assert_called_once_with("test.txt")
        mock_state_store.set.assert_called_once_with("test.txt", b"test content")

    def test_download_from_cloud_error(self, cache_workflow, mock_s3_storage):
        """Test download from cloud with error."""
        mock_s3_storage.download.side_effect = Exception("Test error")
        result = cache_workflow.download_from_cloud("test.txt")
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_upload_to_cloud_success(self, cache_workflow, mock_s3_storage, mock_state_store):
        """Test successful upload to cloud."""
        mock_state_store.get.return_value = b"test content"
        mock_s3_storage.upload.return_value = True

        result = cache_workflow.upload_to_cloud("test.txt")
        assert result["success"] is True
        assert result["data"] == "test.txt"

        mock_state_store.get.assert_called_once_with("test.txt")
        mock_s3_storage.upload.assert_called_once_with("test.txt", b"test content")

    def test_upload_to_cloud_error(self, cache_workflow, mock_state_store):
        """Test upload to cloud with error."""
        mock_state_store.get.side_effect = Exception("Test error")
        result = cache_workflow.upload_to_cloud("test.txt")
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_run_success(self, cache_workflow, mock_s3_storage, mock_state_store):
        """Test successful workflow run."""
        # Setup mocks
        mock_s3_storage.list.return_value = ["file1.txt"]
        mock_state_store.get.return_value = b"test content"
        mock_s3_storage.upload.return_value = True

        # Test run
        result = cache_workflow.run("prefix/")
        assert result["success"] is True
        assert "data" in result
        assert "uploaded" in result["data"]
        assert "failed" in result["data"]

        # Verify calls
        mock_s3_storage.list.assert_called_once_with("prefix/")
        mock_state_store.get.assert_called_once_with("file1.txt")
        mock_s3_storage.upload.assert_called_once_with("file1.txt", b"test content")

    def test_run_error(self, cache_workflow, mock_s3_storage):
        """Test workflow run with error."""
        mock_s3_storage.list.side_effect = Exception("Test error")
        result = cache_workflow.run("prefix/")
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

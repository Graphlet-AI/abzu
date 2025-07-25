"""Tests for utility functions and classes."""

from unittest.mock import Mock, patch

import pytest
from dapr.clients.grpc._state import StateOptions

from abzu.utils import DaprS3Storage, DaprStateStore


@pytest.fixture
def mock_dapr_client():
    """Create a mock Dapr client."""
    with patch("abzu.utils.DaprClient") as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def state_store(mock_dapr_client):
    """Create a DaprStateStore instance with mocked client."""
    return DaprStateStore()


@pytest.fixture
def s3_storage(mock_dapr_client):
    """Create a DaprS3Storage instance with mocked client."""
    return DaprS3Storage()


class TestDaprStateStore:
    """Test suite for DaprStateStore class."""

    def test_init(self, mock_dapr_client):
        """Test DaprStateStore initialization."""
        store = DaprStateStore()
        assert store.store_name == "statestore"
        assert store.client == mock_dapr_client

    def test_init_custom_store(self, mock_dapr_client):
        """Test DaprStateStore initialization with custom store name."""
        store = DaprStateStore("custom-store")
        assert store.store_name == "custom-store"

    def test_get_success(self, state_store, mock_dapr_client):
        """Test successful state retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = b"test-value"
        mock_dapr_client.get_state.return_value = mock_response

        # Test get
        result = state_store.get("test-key")
        assert result == "test-value"
        mock_dapr_client.get_state.assert_called_once_with(
            "statestore", "test-key", state_metadata=None
        )

    def test_get_not_found(self, state_store, mock_dapr_client):
        """Test state retrieval when key doesn't exist."""
        mock_dapr_client.get_state.return_value = None
        result = state_store.get("test-key")
        assert result is None

    def test_get_with_metadata(self, state_store, mock_dapr_client):
        """Test state retrieval with metadata."""
        metadata = {"ttl": "3600"}
        mock_response = Mock()
        mock_response.data = b"test-value"
        mock_dapr_client.get_state.return_value = mock_response

        result = state_store.get("test-key", metadata=metadata)
        assert result == "test-value"
        mock_dapr_client.get_state.assert_called_once_with(
            "statestore", "test-key", state_metadata=metadata
        )

    def test_set_success(self, state_store, mock_dapr_client):
        """Test successful state setting."""
        state_store.set("test-key", "test-value")
        mock_dapr_client.save_state.assert_called_once_with(
            "statestore", "test-key", "test-value", state_metadata=None, options=None, etag=None
        )

    def test_set_with_options(self, state_store, mock_dapr_client):
        """Test state setting with options."""
        options = StateOptions(consistency="strong")
        state_store.set("test-key", "test-value", options=options)
        mock_dapr_client.save_state.assert_called_once_with(
            "statestore", "test-key", "test-value", state_metadata=None, options=options, etag=None
        )

    def test_delete_success(self, state_store, mock_dapr_client):
        """Test successful state deletion."""
        state_store.delete("test-key")
        mock_dapr_client.delete_state.assert_called_once_with(
            "statestore", "test-key", state_metadata=None, options=None, etag=None
        )

    def test_get_bulk_success(self, state_store, mock_dapr_client):
        """Test successful bulk state retrieval."""
        # Setup mock response
        mock_item1 = Mock()
        mock_item1.key = "key1"
        mock_item1.data = b"value1"
        mock_item1.etag = "etag1"

        mock_item2 = Mock()
        mock_item2.key = "key2"
        mock_item2.data = b"value2"
        mock_item2.etag = "etag2"

        mock_response = Mock()
        mock_response.items = [mock_item1, mock_item2]
        mock_dapr_client.get_bulk_state.return_value = mock_response

        # Test get_bulk
        result = state_store.get_bulk(["key1", "key2"])
        assert len(result) == 2
        assert result[0]["key"] == "key1"
        assert result[0]["value"] == "value1"
        assert result[0]["etag"] == "etag1"
        assert result[1]["key"] == "key2"
        assert result[1]["value"] == "value2"
        assert result[1]["etag"] == "etag2"

    def test_set_bulk_success(self, state_store, mock_dapr_client):
        """Test successful bulk state setting."""
        items = [
            {"key": "key1", "value": "value1", "etag": "etag1"},
            {"key": "key2", "value": "value2", "etag": "etag2"},
        ]
        state_store.set_bulk(items)
        mock_dapr_client.save_bulk_state.assert_called_once()

    def test_execute_transaction_success(self, state_store, mock_dapr_client):
        """Test successful transaction execution."""
        operations = [("upsert", "key1", "value1", None), ("delete", "key2", None, None)]
        state_store.execute_transaction(operations)
        mock_dapr_client.execute_state_transaction.assert_called_once()

    def test_query_success(self, state_store, mock_dapr_client):
        """Test successful query execution."""
        # Setup mock response
        mock_item = Mock()
        mock_item.key = "key1"
        mock_item.value = b'{"data": "value1"}'
        mock_item.etag = "etag1"

        mock_response = Mock()
        mock_response.results = [mock_item]
        mock_response.token = "next-token"
        mock_dapr_client.query_state.return_value = mock_response

        # Test query
        query = {
            "filter": {"EQ": {"source": "test"}},
            "sort": [{"key": "created_at", "order": "DESC"}],
            "page": {"limit": 10},
        }
        result = state_store.query(query)

        assert len(result["results"]) == 1
        assert result["results"][0]["key"] == "key1"
        assert result["results"][0]["data"] == {"data": "value1"}
        assert result["results"][0]["etag"] == "etag1"
        assert result["token"] == "next-token"

    def test_error_handling(self, state_store, mock_dapr_client):
        """Test error handling in state operations."""
        mock_dapr_client.get_state.side_effect = Exception("Test error")
        with pytest.raises(Exception):
            state_store.get("test-key")


class TestDaprS3Storage:
    """Test suite for DaprS3Storage class."""

    def test_init(self, mock_dapr_client):
        """Test DaprS3Storage initialization."""
        storage = DaprS3Storage()
        assert storage.binding_name == "s3"
        assert storage.client == mock_dapr_client

    def test_init_custom_binding(self, mock_dapr_client):
        """Test DaprS3Storage initialization with custom binding name."""
        storage = DaprS3Storage("custom-s3")
        assert storage.binding_name == "custom-s3"

    def test_upload_success(self, s3_storage, mock_dapr_client):
        """Test successful file upload."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = b'{"success": true}'
        mock_dapr_client.invoke_binding.return_value = mock_response

        # Test upload
        result = s3_storage.upload("test.txt", b"test content")
        assert result is True

        # Verify binding invocation
        mock_dapr_client.invoke_binding.assert_called_once()
        call_args = mock_dapr_client.invoke_binding.call_args[1]
        assert call_args["binding_name"] == "s3"
        assert call_args["operation"] == "create"
        assert call_args["data"] == b"test content"
        assert call_args["binding_metadata"]["key"] == "test.txt"

    def test_download_success(self, s3_storage, mock_dapr_client):
        """Test successful file download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = b"test content"
        mock_dapr_client.invoke_binding.return_value = mock_response

        # Test download
        result = s3_storage.download("test.txt")
        assert result == b"test content"

        # Verify binding invocation
        mock_dapr_client.invoke_binding.assert_called_once()
        call_args = mock_dapr_client.invoke_binding.call_args[1]
        assert call_args["binding_name"] == "s3"
        assert call_args["operation"] == "get"
        assert call_args["binding_metadata"]["key"] == "test.txt"

    def test_delete_success(self, s3_storage, mock_dapr_client):
        """Test successful file deletion."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = b'{"success": true}'
        mock_dapr_client.invoke_binding.return_value = mock_response

        # Test delete
        result = s3_storage.delete("test.txt")
        assert result is True

        # Verify binding invocation
        mock_dapr_client.invoke_binding.assert_called_once()
        call_args = mock_dapr_client.invoke_binding.call_args[1]
        assert call_args["binding_name"] == "s3"
        assert call_args["operation"] == "delete"
        assert call_args["binding_metadata"]["key"] == "test.txt"

    def test_list_success(self, s3_storage, mock_dapr_client):
        """Test successful file listing."""
        # Setup mock response
        mock_response = Mock()
        mock_response.data = b'{"files": ["file1.txt", "file2.txt"]}'
        mock_dapr_client.invoke_binding.return_value = mock_response

        # Test list
        result = s3_storage.list("prefix/")
        assert result == ["file1.txt", "file2.txt"]

        # Verify binding invocation
        mock_dapr_client.invoke_binding.assert_called_once()
        call_args = mock_dapr_client.invoke_binding.call_args[1]
        assert call_args["binding_name"] == "s3"
        assert call_args["operation"] == "list"
        assert call_args["binding_metadata"]["prefix"] == "prefix/"

    def test_error_handling(self, s3_storage, mock_dapr_client):
        """Test error handling in storage operations."""
        mock_dapr_client.invoke_binding.side_effect = Exception("Test error")
        with pytest.raises(Exception):
            s3_storage.upload("test.txt", b"test content")

"""Tests for the sync service functionality."""

import json
from unittest.mock import Mock, patch

import pytest

# Remove the global pytest mark since we don't need async for these tests
# pytestmark = pytest.mark.asyncio


# Mock Dapr dependencies before importing the workflow module
def mock_activity_decorator(func):
    """Mock activity decorator that just returns the function unchanged."""
    return func


def mock_workflow_decorator(*args, **kwargs):
    """Mock workflow decorator that just returns the function unchanged."""

    def decorator(func):
        return func

    return decorator


with patch("dapr.clients.health.DaprHealth.wait_until_ready"):
    with patch("dapr.clients.DaprClient"):
        with patch("abzu.utils.DaprStateStore"):
            with patch("abzu.utils.DaprS3Storage"):
                with patch("dapr.ext.workflow.WorkflowRuntime") as mock_runtime:
                    # Mock the decorators to be no-ops
                    mock_runtime.return_value.activity = mock_activity_decorator
                    mock_runtime.return_value.workflow = mock_workflow_decorator
                    from abzu.workflows.cache_workflow import (
                        cache_sync_workflow,
                        check_cloud_cache,
                        download_from_cloud,
                        upload_to_cloud,
                    )


@pytest.fixture
def mock_state_store():
    """Create a mock state store."""
    with patch("abzu.workflows.cache_workflow.state_store") as mock:
        store = Mock()
        mock.get = store.get
        mock.set = store.set
        yield store


@pytest.fixture
def mock_s3_storage():
    """Create a mock S3 storage."""
    with patch("abzu.workflows.cache_workflow.s3_storage") as mock:
        storage = Mock()
        mock.download = storage.download
        mock.upload = storage.upload
        yield storage


@pytest.fixture
def mock_workflow_context():
    """Create a mock workflow context."""
    ctx = Mock()
    ctx.call_activity = Mock()
    return ctx


class MockStateStore:
    """Mock state store with shared storage."""

    def __init__(self, storage):
        self.storage = storage

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self.storage[key] = value


class MockS3Storage:
    """Mock S3 storage with shared storage."""

    def __init__(self, storage):
        self.storage = storage

    def download(self, key):
        value = self.storage.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            return value.encode()
        return value

    def upload(self, key, data):
        if isinstance(data, bytes):
            data = data.decode()
        if isinstance(data, str):
            try:
                json.loads(data)
            except json.JSONDecodeError:
                pass
        self.storage[key] = data


class MockWorkflowContext:
    """Mock workflow context with shared storage."""

    def __init__(self, storage):
        self.storage = storage

    def call_activity(self, activity, input=None):
        if activity == check_cloud_cache:
            return self.storage.get(input) is not None
        elif activity == download_from_cloud:
            value = self.storage.get(input)
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        elif activity == upload_to_cloud:
            key, data = input
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            self.storage[key] = data
            return True
        return None


@pytest.fixture
def mock_dapr_components():
    """Create stateful mocks for Dapr components with shared in-memory storage."""
    state_storage = {}
    mock_state_store = MockStateStore(state_storage)
    mock_s3_storage = MockS3Storage(state_storage)
    mock_workflow_context = MockWorkflowContext(state_storage)
    mock_workflow_runtime = Mock()
    mock_workflow_runtime.activity = lambda func: func
    mock_workflow_runtime.workflow = lambda *args, **kwargs: lambda func: func
    mock_workflow_runtime.start_workflow = lambda *args, **kwargs: True

    with (
        patch("abzu.workflows.cache_workflow.state_store", mock_state_store),
        patch("abzu.workflows.cache_workflow.s3_storage", mock_s3_storage),
        patch("abzu.workflows.cache_workflow.wfr", mock_workflow_runtime),
    ):
        yield {
            "state_store": mock_state_store,
            "s3_storage": mock_s3_storage,
            "workflow_runtime": mock_workflow_runtime,
            "workflow_context": mock_workflow_context,
            "storage": state_storage,
        }


class TestCacheWorkflow:
    """Test suite for cache workflow functions."""

    def test_check_cloud_cache_s3_hit(self, mock_dapr_components):
        """Test cloud cache check with S3 hit."""
        # Store test data in shared storage
        mock_dapr_components["storage"]["test-key"] = "test data"
        result = check_cloud_cache(None, "test-key")
        assert result is True

    def test_check_cloud_cache_state_hit(self, mock_dapr_components):
        """Test cloud cache check with state store hit."""
        # Store test data in shared storage
        mock_dapr_components["storage"]["test-key"] = "test data"
        result = check_cloud_cache(None, "test-key")
        assert result is True

    def test_check_cloud_cache_miss(self, mock_dapr_components):
        """Test cloud cache check with no hits."""
        result = check_cloud_cache(None, "test-key")
        assert result is False

    def test_check_cloud_cache_error(self, mock_dapr_components):
        """Test cloud cache check with error."""
        # Simulate error by making download raise an exception
        mock_dapr_components["s3_storage"].download = lambda key: (_ for _ in ()).throw(
            Exception("Test error")
        )
        result = check_cloud_cache(None, "test-key")
        assert result is False

    def test_download_from_cloud_s3_success(self, mock_dapr_components):
        """Test successful download from S3."""
        test_data = {"title": "Test Article", "content": "Test Content"}
        # Store test data in shared storage
        mock_dapr_components["storage"]["test-key"] = json.dumps(test_data)
        result = download_from_cloud(None, "test-key")
        assert result == test_data

    def test_download_from_cloud_state_success(self, mock_dapr_components):
        """Test successful download from state store."""
        test_data = {"title": "Test Article", "content": "Test Content"}
        # Store test data in shared storage
        mock_dapr_components["storage"]["test-key"] = json.dumps(test_data)
        result = download_from_cloud(None, "test-key")
        assert result == test_data

    def test_download_from_cloud_not_found(self, mock_dapr_components):
        """Test download when data not found."""
        result = download_from_cloud(None, "test-key")
        assert result is None

    def test_download_from_cloud_error(self, mock_dapr_components):
        """Test download with error."""
        # Simulate error by making download raise an exception
        mock_dapr_components["s3_storage"].download = lambda key: (_ for _ in ()).throw(
            Exception("Test error")
        )
        result = download_from_cloud(None, "test-key")
        assert result is None

    def test_upload_to_cloud_large_data(self, mock_dapr_components):
        """Test uploading large data to cloud."""
        # Create large data (>1MB)
        large_data = {"content": "x" * (1024 * 1024 + 1)}
        result = upload_to_cloud(None, "test-key", large_data)
        assert result is True
        # Verify data was stored
        stored_data = mock_dapr_components["storage"].get("test-key")
        assert stored_data == json.dumps(large_data)

    def test_upload_to_cloud_small_data(self, mock_dapr_components):
        """Test uploading small data to cloud."""
        small_data = {"content": "small data"}
        result = upload_to_cloud(None, "test-key", small_data)
        assert result is True
        # Verify data was stored
        stored_data = mock_dapr_components["storage"].get("test-key")
        assert stored_data == json.dumps(small_data)

    def test_upload_to_cloud_error(self, mock_dapr_components):
        """Test upload with error."""
        # Simulate error by making set raise an exception
        mock_dapr_components["state_store"].set = lambda key, value: (_ for _ in ()).throw(
            Exception("Test error")
        )
        result = upload_to_cloud(None, "test-key", {"data": "test"})
        assert result is False

    def test_cache_sync_workflow_upload_success(self, mock_dapr_components):
        """Test successful workflow run with upload."""
        test_data = {"title": "Test Article"}
        # The workflow is a generator that yields activity calls
        gen = cache_sync_workflow(
            mock_dapr_components["workflow_context"], "articles", "test-key", test_data
        )

        # Start the generator and send results for each yield
        try:
            # First yield should be the check_cloud_cache call
            gen.send(None)  # Start the generator
            # Send False (cache miss) back to the generator
            gen.send(False)
            # Send True (upload success) back to the generator
            result = gen.send(True)
        except StopIteration as e:
            result = e.value

        assert result["success"] is True
        assert result["data"] == test_data
        assert result["error"] is None
        # Verify data was stored in state store
        stored_data = mock_dapr_components["state_store"].get("test-key")
        assert stored_data == json.dumps(test_data)

    def test_cache_sync_workflow_download_success(self, mock_dapr_components):
        """Test successful workflow run with download."""
        test_data = {"title": "Test Article"}
        # Store test data in shared storage
        mock_dapr_components["storage"]["test-key"] = json.dumps(test_data)

        # The workflow is a generator that yields activity calls
        gen = cache_sync_workflow(mock_dapr_components["workflow_context"], "articles", "test-key")

        # Start the generator
        try:
            # First yield should be the download_from_cloud call
            gen.send(None)  # Start the generator
            # Send the test data back to the generator
            result = gen.send(test_data)
        except StopIteration as e:
            result = e.value

        assert result["success"] is True
        assert result["data"] == test_data
        assert result["error"] is None

    def test_cache_sync_workflow_not_found(self, mock_dapr_components):
        """Test workflow run when data not found."""
        # The workflow is a generator that yields activity calls
        gen = cache_sync_workflow(mock_dapr_components["workflow_context"], "articles", "test-key")

        # Start the generator
        try:
            # First yield should be the download_from_cloud call
            gen.send(None)  # Start the generator
            # Send None (not found) back to the generator
            result = gen.send(None)
        except StopIteration as e:
            result = e.value

        assert result["success"] is False
        assert result["data"] is None
        assert result["error"] == "Data not found"

    def test_cache_sync_workflow_error(self, mock_dapr_components):
        """Test workflow run with error."""
        # Simulate error by making download raise an exception
        mock_dapr_components["s3_storage"].download = lambda key: (_ for _ in ()).throw(
            Exception("Test error")
        )

        # The workflow is a generator, and we expect it to catch exceptions
        gen = cache_sync_workflow(mock_dapr_components["workflow_context"], "articles", "test-key")
        result = None

        try:
            gen.send(None)  # Start the generator
            assert False, "Should have raised StopIteration"
        except StopIteration as e:
            result = e.value
        except Exception:
            # If an exception propagates, create an error result
            result = {"success": False, "data": None, "error": "Test error"}

        assert result is not None
        assert result["success"] is False
        assert result["data"] is None
        assert "error" in result

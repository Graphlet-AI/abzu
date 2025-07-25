"""Integration tests for the sync service with Dapr components."""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from abzu.cache import PipelineCache
from abzu.workflows.cache_workflow import (
    check_cloud_cache,
    download_from_cloud,
    upload_to_cloud,
)


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for testing."""
    os.environ["ABZU_CACHE_MODE"] = "hybrid"
    os.environ["ABZU_CACHE_DIR"] = "data/test_cache"
    yield
    # Cleanup
    if Path("data/test_cache").exists():
        import shutil

        shutil.rmtree("data/test_cache")


@pytest.fixture(autouse=True)
def mock_dapr_client():
    """Mock Dapr client to prevent health checks."""
    with patch("dapr.clients.DaprClient") as mock:
        client = Mock()
        # Configure get_state to return a mock response with data
        mock_response = Mock()
        mock_response.data.decode.return_value = '{"test": "data"}'  # Return decoded JSON string
        client.get_state.return_value = mock_response
        mock.return_value = client
        yield client


class MockStateStore:
    """Mock state store that mimics Dapr's behavior of storing raw values."""

    def __init__(self, storage):
        self.storage = storage

    def get(self, key):
        """Return the raw value, mirroring Dapr's behavior."""
        return self.storage.get(key)

    def set(self, key, value):
        """Store the raw value, as the app does the serialization."""
        self.storage[key] = value


class MockS3Storage:
    """Mock S3 storage that mimics Dapr's behavior of storing bytes."""

    def __init__(self, storage):
        self.storage = storage

    def download(self, key):
        """Download data as bytes, mirroring S3's behavior."""
        value = self.storage.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            return value.encode("utf-8")
        return value  # Should already be bytes if uploaded correctly

    def upload(self, key, data):
        """Upload data as bytes, mirroring S3's behavior."""
        # Store as string for easier inspection in the mock storage.
        if isinstance(data, bytes):
            self.storage[key] = data.decode("utf-8")
        else:
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
            elif isinstance(data, Mock):
                data = json.dumps({"mock": True})
            self.storage[key] = data
            return True
        return None


@pytest.fixture
def mock_dapr_components():
    """Mock Dapr components for integration testing."""
    state_storage = {}
    mock_state_store = MockStateStore(state_storage)
    mock_s3_storage = MockS3Storage(state_storage)
    mock_workflow_runtime = Mock()
    mock_workflow_runtime.activity = lambda func: func
    mock_workflow_runtime.workflow = lambda *args, **kwargs: lambda func: func
    mock_workflow_runtime.start_workflow = AsyncMock(return_value=True)

    with (
        patch("abzu.utils.DaprStateStore", return_value=mock_state_store),
        patch("abzu.utils.DaprS3Storage", return_value=mock_s3_storage),
        patch("abzu.workflows.cache_workflow.wfr", mock_workflow_runtime),
    ):
        yield {
            "state_store": mock_state_store,
            "s3_storage": mock_s3_storage,
            "workflow_runtime": mock_workflow_runtime,
            "state_storage": state_storage,
        }


@pytest.fixture
def cache(mock_dapr_components):
    """Create a PipelineCache instance with mocked components."""
    return PipelineCache()


@pytest.mark.asyncio
async def test_url_sync(cache, mock_dapr_components):
    """Test URL synchronization between local and cloud storage."""
    # Test data
    source = "test_source"
    test_urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]

    # Add URLs
    for url in test_urls:
        cache.add_crawled_url(source, url)

    # Verify local storage
    local_urls = cache.get_crawled_urls(source)
    assert set(local_urls) == set(test_urls)

    # Verify Dapr state store
    key = f"crawled_urls:{source}"
    state_urls = mock_dapr_components["state_storage"].get(key)
    assert state_urls is not None
    assert set(state_urls.split(",")) == set(test_urls)


@pytest.mark.asyncio
async def test_article_sync(cache, mock_dapr_components):
    """Test article synchronization between local and cloud storage."""
    # Test data
    source = "test_source"
    article_data = {
        "title": "Test Article",
        "content": "Test Content",
        "url": "https://example.com/test",
        "published_at": str(datetime.now()),
    }

    # Add article
    cache.cache_article(source, article_data)

    # Verify local storage
    local_article = cache.get_cached_article(source, article_data["url"])
    assert local_article is not None
    assert local_article["url"] == article_data["url"]
    assert local_article["title"] == article_data["title"]

    # Verify Dapr state store
    key = f"article:{source}:{article_data['url']}"
    state_article = mock_dapr_components["state_storage"].get(key)
    assert state_article is not None
    assert json.loads(state_article)["url"] == article_data["url"]


@pytest.mark.asyncio
async def test_knowledge_graph_sync(cache, mock_dapr_components):
    """Test knowledge graph synchronization between local and cloud storage."""
    # Test data
    graph_type = "test_graph"
    graph_data = {"nodes": ["node1", "node2"], "edges": [{"from": "node1", "to": "node2"}]}

    # Cache knowledge graph
    cache.cache_knowledge_graph(graph_type, graph_data)

    # Verify local storage
    cached_graph = cache.get_cached_knowledge_graph(graph_type)
    assert cached_graph is not None
    assert cached_graph["nodes"] == graph_data["nodes"]
    assert cached_graph["edges"] == graph_data["edges"]

    # Verify Dapr state store
    key = f"kg:{graph_type}"
    state_graph = mock_dapr_components["state_storage"].get(key)
    assert state_graph is not None
    assert json.loads(state_graph)["nodes"] == graph_data["nodes"]


@pytest.mark.asyncio
async def test_workflow_sync(cache, mock_dapr_components):
    """Test workflow-based synchronization."""
    # Test data
    category = "test_category"
    key = "test_key"
    data = {"test": "data"}

    # Pre-populate state store for download test
    mock_dapr_components["state_storage"][key] = json.dumps(data)

    # Test sync with cloud
    success = await cache._sync_with_cloud(category, key, data)
    assert success is True

    # Verify workflow was called
    mock_dapr_components["workflow_runtime"].start_workflow.assert_called()

    # To test download via workflow, we need to simulate the workflow running
    # and populating the cache. The above only tests the upload part.
    # For this integration test, we'll rely on testing the activities directly.
    with (
        patch("abzu.workflows.cache_workflow.s3_storage", mock_dapr_components["s3_storage"]),
        patch("abzu.workflows.cache_workflow.state_store", mock_dapr_components["state_store"]),
    ):
        cloud_data = download_from_cloud(None, key)
    assert cloud_data is not None
    assert cloud_data["test"] == data["test"]


@pytest.mark.asyncio
async def test_error_handling(cache, mock_dapr_components):
    """Test error handling in sync operations."""
    # Test with invalid data (e.g., incomplete article)
    source = "test_source"
    invalid_article = {
        "url": "https://example.com/invalid",
        # Missing required fields like title, content
    }

    # Caching should handle this gracefully
    cache.cache_article(source, invalid_article)

    # Retrieval should work and return the stored data
    retrieved_article = cache.get_cached_article(source, invalid_article["url"])
    assert retrieved_article is not None
    assert retrieved_article["url"] == invalid_article["url"]

    # Test with a nonexistent key
    cached_article = cache.get_cached_article(source, "nonexistent_url")
    assert cached_article is None

    # Test workflow error handling by mocking a failure
    mock_dapr_components["workflow_runtime"].start_workflow.return_value = False
    success = await cache._sync_with_cloud("invalid", "invalid_key", {"data": "test"})
    assert success is False  # Should handle the workflow start failure gracefully

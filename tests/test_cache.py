"""Tests for the caching system."""

import json
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Mock Dapr dependencies before importing any Dapr-dependent code
mock_state_store = Mock()
mock_s3_storage = Mock()
mock_workflow_runtime = Mock()
mock_workflow_runtime.wfr = AsyncMock()
mock_workflow_runtime.cache_sync_workflow = "cache_sync_workflow"

with patch("dapr.clients.health.DaprHealth.wait_until_ready"):
    with patch("dapr.clients.DaprClient"):
        with patch("abzu.utils.DaprStateStore", return_value=mock_state_store):
            with patch("abzu.utils.DaprS3Storage", return_value=mock_s3_storage):
                with patch(
                    "abzu.cache.importlib.import_module", return_value=mock_workflow_runtime
                ):
                    from abzu.cache import PipelineCache


@pytest.fixture
def mock_dapr_client():
    """Create a mock Dapr client."""
    with patch("abzu.utils.DaprClient") as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_workflow_runtime_fixture():
    """Create a mock workflow runtime."""
    with patch("abzu.cache.importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.wfr = AsyncMock()
        mock_module.cache_sync_workflow = "cache_sync_workflow"
        mock_import.return_value = mock_module
        yield mock_module


@pytest.fixture
def mock_state_store_fixture(mock_dapr_client):
    """Create a mock state store."""
    with patch("abzu.utils.DaprStateStore") as mock:
        store = Mock()
        mock.return_value = store
        yield store


@pytest.fixture
def mock_s3_storage_fixture():
    """Create a mock S3 storage."""
    with patch("abzu.utils.DaprS3Storage") as mock:
        storage = Mock()
        mock.return_value = storage
        yield storage


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


class TestPipelineCache:
    """Test suite for PipelineCache class."""

    @pytest.mark.parametrize(
        "mode,expected_components",
        [
            ("none", []),
            ("local", ["state_store"]),
            ("hybrid", ["state_store", "s3_storage", "workflow"]),
        ],
    )
    def test_init(
        self,
        mode,
        expected_components,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_state_store_fixture,
        mock_s3_storage_fixture,
        mock_dapr_client,
    ):
        """Test cache initialization with different modes."""
        monkeypatch.setenv("ABZU_CACHE_MODE", mode)
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        assert cache.mode == mode
        assert cache.base_dir == temp_cache_dir

        # Check components initialization
        if "state_store" in expected_components:
            assert cache.state_store is not None
        if "s3_storage" in expected_components:
            assert cache.s3_storage is not None
        if "workflow" in expected_components:
            assert hasattr(cache, "wfr")

    def test_get_crawled_urls_local(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test getting crawled URLs in local mode."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        mock_state_store_fixture.get.return_value = "url1,url2,url3"

        urls = cache.get_crawled_urls("test_source")
        assert urls == {"url1", "url2", "url3"}
        mock_state_store_fixture.get.assert_called_once_with("crawled_urls:test_source")

    def test_get_crawled_urls_hybrid(
        self,
        mock_state_store_fixture,
        mock_s3_storage_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test getting crawled URLs in hybrid mode."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "hybrid")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        mock_state_store_fixture.get.return_value = "url1,url2,url3"

        urls = cache.get_crawled_urls("test_source")
        assert urls == {"url1", "url2", "url3"}
        mock_state_store_fixture.get.assert_called_once_with("crawled_urls:test_source")

    def test_add_crawled_url(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test adding a crawled URL."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        mock_state_store_fixture.get.return_value = "url1,url2"

        cache.add_crawled_url("test_source", "url3")
        # Sort URLs before comparison to ensure order-independent comparison
        expected_urls = sorted(["url1", "url2", "url3"])
        actual_urls = sorted(mock_state_store_fixture.set.call_args[0][1].split(","))
        assert actual_urls == expected_urls
        mock_state_store_fixture.set.assert_called_once()

    def test_cache_article(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test caching an article."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        article = {"url": "http://test.com", "title": "Test Article"}

        cache.cache_article("test_source", article)
        mock_state_store_fixture.set.assert_called_once()

    def test_get_cached_article(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test getting a cached article."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        article = {"url": "http://test.com", "title": "Test Article"}
        mock_state_store_fixture.get.return_value = json.dumps(article)

        result = cache.get_cached_article("test_source", "http://test.com")
        assert result == article
        mock_state_store_fixture.get.assert_called_once_with("article:test_source:http://test.com")

    def test_cache_knowledge_graph(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test caching knowledge graph data."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        graph_data: dict[str, list[Any]] = {"nodes": [], "edges": []}

        cache.cache_knowledge_graph("test_graph", graph_data)
        mock_state_store_fixture.set.assert_called_once()

    def test_get_cached_knowledge_graph(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test getting cached knowledge graph data."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        graph_data: dict[str, list[Any]] = {"nodes": [], "edges": []}
        mock_state_store_fixture.get.return_value = json.dumps(graph_data)

        result = cache.get_cached_knowledge_graph("test_graph")
        assert result == graph_data
        mock_state_store_fixture.get.assert_called_once_with("kg:test_graph")

    def test_cache_financial_data(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test caching financial data."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "hybrid")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        financial_data = {"price": 100, "volume": 1000}

        cache.cache_financial_data("price", "AAPL", financial_data)
        mock_state_store_fixture.set.assert_called_once()

    def test_get_cached_financial_data(
        self,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test getting cached financial data."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "hybrid")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        financial_data = {"price": 100, "volume": 1000}
        mock_state_store_fixture.get.return_value = str(financial_data)

        result = cache.get_cached_financial_data("price", "AAPL")
        assert result == financial_data
        mock_state_store_fixture.get.assert_called_once_with("financial:price:AAPL")

    def test_pull_from_cloud(
        self,
        mock_s3_storage_fixture,
        mock_state_store_fixture,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_dapr_client,
    ):
        """Test pulling data from cloud storage."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "hybrid")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        mock_s3_storage_fixture.list_keys.return_value = ["article:test:url"]
        mock_s3_storage_fixture.download.return_value = b'{"title": "Test"}'

        cache.pull_from_cloud()
        mock_s3_storage_fixture.list_keys.assert_called_once()
        mock_s3_storage_fixture.download.assert_called_once_with("article:test:url")
        mock_state_store_fixture.set.assert_called_once()

    def test_local_file_fallback(
        self,
        temp_cache_dir,
        monkeypatch,
        mock_workflow_runtime_fixture,
        mock_state_store_fixture,
        mock_dapr_client,
    ):
        """Test local file fallback when Dapr is not available."""
        monkeypatch.setenv("ABZU_CACHE_MODE", "local")
        monkeypatch.setenv("ABZU_CACHE_DIR", str(temp_cache_dir))

        cache = PipelineCache()
        article = {"url": "http://test.com", "title": "Test Article"}

        # Save to local file
        cache.cache_article("test_source", article)

        # Verify file exists
        file_path = temp_cache_dir / "articles" / "article:test_source:http://test.com.jsonl"
        assert file_path.exists()

        # Read and verify content
        with open(file_path, "r") as f:
            content = json.loads(f.read().strip())
            assert content == article

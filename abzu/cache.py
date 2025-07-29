"""Caching strategy for the Abzu pipeline."""

import asyncio

# Workflow module will be imported lazily so that any monkey-patch that happens
# before the first PipelineCache instance is created is taken into account.
import importlib
import inspect
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Coroutine, Dict, Literal, Optional, Set, cast

# Import utilities without binding the patch-able classes/functions at module import
# so that runtime monkey-patching (e.g. in the test-suite) is correctly respected.
from abzu import utils as _abzu_utils
from abzu.utils import get_cache_mode, load_jsonl, save_jsonl

logger = logging.getLogger(__name__)

CacheMode = Literal["none", "local", "hybrid"]


class PipelineCache:
    """Cache manager for the Abzu pipeline."""

    def __init__(self) -> None:
        self.mode: CacheMode = cast(CacheMode, get_cache_mode())
        self.base_dir = Path(os.environ.get("ABZU_CACHE_DIR", "data/cache"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Dynamically resolve (possibly patched) workflow runtime and cache workflow
        cache_workflow_module = importlib.import_module("abzu.workflows.cache_workflow")
        self.wfr = cache_workflow_module.wfr
        self.cache_sync_workflow = cache_workflow_module.cache_sync_workflow

        # Placeholders for Dapr components; initialise lazily to prevent
        # expensive side-car health-checks during import/collection time.
        self._state_store: Optional[_abzu_utils.DaprStateStore] = None
        self._s3_storage: Optional[_abzu_utils.DaprS3Storage] = None

    def _get_local_path(self, category: str, key: str) -> Path:
        """Get local file path for a cache entry."""
        return self.base_dir / category / f"{key}.jsonl"

    def _save_local(self, path: Path, data: Any) -> None:
        """Save data to local file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, list):
            save_jsonl(data, path)
        else:
            save_jsonl([data], path)

    def _load_local(self, path: Path) -> Optional[Any]:
        """Load data from local file."""
        if not path.exists():
            return None
        data = load_jsonl(path)
        return data[0] if len(data) == 1 else data

    async def _sync_with_cloud(
        self, category: str, key: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Sync data with cloud using workflow."""
        if self.mode != "hybrid":
            return True

        try:
            # Start workflow
            instance_id = f"cache-sync-{category}-{key}-{datetime.now().timestamp()}"
            success = await self.wfr.start_workflow(
                self.cache_sync_workflow, instance_id, category, key, data
            )
            return cast(bool, success)
        except Exception as e:
            logger.error(f"Failed to start cache sync workflow: {e}")
            return False

    def get_crawled_urls(self, source: str) -> Set[str]:
        """Get set of already crawled URLs for a source."""
        key = f"crawled_urls:{source}"

        # Try local Dapr first if enabled
        if self.mode in ("local", "hybrid"):
            urls = self.state_store.get(key)
            if urls:
                return set(urls.split(","))

            # Try cloud in hybrid mode
            if self.mode == "hybrid":
                # Start workflow to check cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"urls-{source}-{datetime.now().timestamp()}",
                    "urls",
                    key,
                )

        # Fall back to local file
        path = self._get_local_path("urls", source)
        data = self._load_local(path)
        return set(data.get("urls", [])) if data else set()

    def add_crawled_url(self, source: str, url: str) -> None:
        """Add a URL to the crawled set for a source."""
        key = f"crawled_urls:{source}"
        urls = self.get_crawled_urls(source)
        urls.add(url)

        # Save to local Dapr if enabled
        if self.mode in ("local", "hybrid"):
            self.state_store.set(key, ",".join(urls))
            if self.mode == "hybrid":
                # Start workflow to sync with cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"urls-{source}-{datetime.now().timestamp()}",
                    "urls",
                    key,
                    {"urls": list(urls)},
                )

        # Always save to local file
        self._save_local(self._get_local_path("urls", source), {"urls": list(urls)})

    def cache_article(self, source: str, article: Dict[str, Any]) -> None:
        """Cache a processed article."""
        key = f"article:{source}:{article['url']}"

        # Save to local Dapr if enabled
        if self.mode in ("local", "hybrid"):
            self.state_store.set(key, json.dumps(article))
            if self.mode == "hybrid":
                # Start workflow to sync with cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"article-{source}-{article['url']}-{datetime.now().timestamp()}",
                    "articles",
                    key,
                    article,
                )

        # Always save to local file
        self._save_local(self._get_local_path("articles", key), article)

    def get_cached_article(self, source: str, url: str) -> Optional[Dict[str, Any]]:
        """Get a cached article if it exists."""
        key = f"article:{source}:{url}"

        # Try local Dapr first if enabled
        if self.mode in ("local", "hybrid"):
            article = self.state_store.get(key)
            if article:
                return cast(Dict[str, Any], json.loads(article))

            # Try cloud in hybrid mode
            if self.mode == "hybrid":
                # Start workflow to check cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"article-{source}-{url}-{datetime.now().timestamp()}",
                    "articles",
                    key,
                )

        # Fall back to local file
        return cast(
            Optional[Dict[str, Any]], self._load_local(self._get_local_path("articles", key))
        )

    def cache_knowledge_graph(self, graph_type: str, data: Dict[str, Any]) -> None:
        """Cache knowledge graph data."""
        key = f"kg:{graph_type}"

        # Save to local Dapr if enabled
        if self.mode in ("local", "hybrid"):
            self.state_store.set(key, json.dumps(data))
            if self.mode == "hybrid":
                # Start workflow to sync with cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"kg-{graph_type}-{datetime.now().timestamp()}",
                    "kg",
                    key,
                    data,
                )

        # Always save to local file
        self._save_local(self._get_local_path("kg", key), data)

    def get_cached_knowledge_graph(self, graph_type: str) -> Optional[Dict[str, Any]]:
        """Get cached knowledge graph data."""
        key = f"kg:{graph_type}"

        # Try local Dapr first if enabled
        if self.mode in ("local", "hybrid"):
            data = self.state_store.get(key)
            if data:
                return cast(Dict[str, Any], json.loads(data))

            # Try cloud in hybrid mode
            if self.mode == "hybrid":
                # Start workflow to check cloud
                self._safe_start_workflow(
                    self.cache_sync_workflow,
                    f"kg-{graph_type}-{datetime.now().timestamp()}",
                    "kg",
                    key,
                )

        # Fall back to local file
        return cast(Optional[Dict[str, Any]], self._load_local(self._get_local_path("kg", key)))

    def cache_financial_data(self, data_type: str, ticker: str, data: Dict[str, Any]) -> None:
        """Cache financial data for a ticker."""
        if self.mode == "hybrid":
            key = f"financial:{data_type}:{ticker}"
            self.state_store.set(key, str(data))
            # Start workflow to sync with cloud
            self._safe_start_workflow(
                self.cache_sync_workflow,
                f"financial-{data_type}-{ticker}-{datetime.now().timestamp()}",
                "financial",
                key,
                data,
            )

    def get_cached_financial_data(self, data_type: str, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached financial data for a ticker."""
        if self.mode == "hybrid":
            key = f"financial:{data_type}:{ticker}"
            data = self.state_store.get(key)
            if data:
                return cast(Dict[str, Any], eval(data))

            # Start workflow to check cloud
            self._safe_start_workflow(
                self.cache_sync_workflow,
                f"financial-{data_type}-{ticker}-{datetime.now().timestamp()}",
                "financial",
                key,
            )
        return None

    def pull_from_cloud(self) -> None:
        """Pull updates from cloud storage to local cache."""
        if self.mode != "hybrid":
            return

        try:
            # Get list of keys from cloud
            cloud_keys = self.s3_storage.list_keys()

            for key in cloud_keys:
                # Download and update local cache
                data = self.s3_storage.download(key)
                if data:
                    # Update local Dapr
                    self.state_store.set(key, data.decode())
                    # Update local file
                    category = key.split(":")[0]
                    self._save_local(self._get_local_path(category, key), json.loads(data))

        except Exception as e:
            logger.error(f"Failed to pull from cloud: {e}")

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _safe_start_workflow(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        """Start a workflow and *safely* handle both sync and async variants.

        In production the Dapr workflow runtime's ``start_workflow`` method is
        synchronous, but in the test-suite it is patched with an ``AsyncMock``
        to keep assertions simple.  Calling an *async* mock from synchronous
        code produces `RuntimeWarning: coroutine was never awaited` unless we
        detect and schedule it.  This helper delegates to the underlying
        ``start_workflow`` and, if the returned value is awaitable, schedules
        it on the running event-loop (or executes it immediately when no loop
        is active).  Any exception during startup is logged and swallowed so
        that cache operations remain non-fatal.
        """

        try:
            maybe_coro = self.wfr.start_workflow(*args, **kwargs)
            if inspect.isawaitable(maybe_coro):
                try:
                    asyncio.get_running_loop().create_task(maybe_coro)  # type: ignore[arg-type]
                except RuntimeError:
                    # Execute the coroutine to completion when no event-loop is running.
                    asyncio.run(cast(Coroutine[Any, Any, Any], maybe_coro))  # pragma: no cover
        except Exception as exc:  # pragma: no cover – should never fail in tests
            logger.warning("Failed to start workflow asynchronously: %s", exc)

    # ------------------------------------------------------------------
    # Lazy Dapr component accessors
    # ------------------------------------------------------------------

    @property
    def state_store(self) -> _abzu_utils.DaprStateStore:
        if self._state_store is None:
            self._state_store = _abzu_utils.DaprStateStore()
        return self._state_store

    @property
    def s3_storage(self) -> _abzu_utils.DaprS3Storage:
        if self._s3_storage is None:
            self._s3_storage = _abzu_utils.DaprS3Storage()
        return self._s3_storage


# Global cache instance
# Instantiation is wrapped in a try/except so that importing "abzu.cache" does
# not fail in environments where Dapr (or any other optional dependency) is
# missing. Tests or applications that need a cache instance can still create
# their own `PipelineCache()` without relying on this global.
try:
    pipeline_cache = PipelineCache()
except Exception as _e:  # pragma: no cover
    logger.warning("Failed to initialize default PipelineCache instance: %s", _e)
    pipeline_cache = None  # type: ignore

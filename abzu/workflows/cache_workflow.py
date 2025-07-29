"""Cache workflow implementation for Abzu."""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Generator, Optional, TypedDict, cast

import dapr.ext.workflow as wf

from abzu.utils import DaprS3Storage, DaprStateStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy, patch-friendly Dapr component resolution
# ---------------------------------------------------------------------------

# These globals will be initialised lazily the first time they are needed.
# Tests can monkey-patch them **after** importing this module but **before** the
# first activity executes – avoiding real Dapr network calls during import.

state_store: Optional[DaprStateStore] = None
s3_storage: Optional[DaprS3Storage] = None


def _ensure_clients() -> None:  # noqa: D401
    """Initialise Dapr clients only when first needed.

    Doing this lazily prevents connection attempts to a running Dapr sidecar
    during test collection (which causes timeouts when the sidecar isn't
    present). If the globals have been monkey-patched by the test-suite, they
    will already be non-``None`` and this function becomes a no-op.
    """

    global state_store, s3_storage

    if state_store is None:
        state_store = DaprStateStore()
    if s3_storage is None:
        s3_storage = DaprS3Storage()


# Initialize workflow runtime
wfr = wf.WorkflowRuntime()


class WorkflowResponse(TypedDict):
    """Response type for workflow operations."""

    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]


@wfr.activity
def check_cloud_cache(ctx: wf.WorkflowActivityContext, key: str) -> bool:
    """Check if data exists in cloud cache."""
    _ensure_clients()
    ss = cast(DaprS3Storage, s3_storage)
    st = cast(DaprStateStore, state_store)
    try:
        # Try to get from S3 first
        s3_data = ss.download(key)
        if s3_data:
            return True

        # Then check state store
        store_data = st.get(key)
        return store_data is not None
    except Exception as e:
        logger.error(f"Failed to check cloud cache: {e}")
        return False


# Expose undecorated implementation for test code (decorator returns a wrapper)
if hasattr(check_cloud_cache, "__wrapped__"):
    check_cloud_cache = cast(Callable[..., Any], check_cloud_cache.__wrapped__)


@wfr.activity
def download_from_cloud(ctx: wf.WorkflowActivityContext, key: str) -> Optional[Dict[str, Any]]:
    """Download data from cloud cache."""
    _ensure_clients()
    ss = cast(DaprS3Storage, s3_storage)
    st = cast(DaprStateStore, state_store)
    try:
        # Try S3 first
        s3_data = ss.download(key)
        if s3_data:
            return cast(Dict[str, Any], json.loads(s3_data.decode()))

        # Then try state store
        store_data = st.get(key)
        return json.loads(store_data) if store_data else None
    except Exception as e:
        logger.error(f"Failed to download from cloud: {e}")
        return None


# Expose undecorated implementation for test code
if hasattr(download_from_cloud, "__wrapped__"):
    download_from_cloud = cast(Callable[..., Any], download_from_cloud.__wrapped__)


@wfr.activity
def upload_to_cloud(ctx: wf.WorkflowActivityContext, key: str, data: Dict[str, Any]) -> bool:
    """Upload data to cloud cache."""
    _ensure_clients()
    ss = cast(DaprS3Storage, s3_storage)
    st = cast(DaprStateStore, state_store)
    try:
        json_data = json.dumps(data)
        # Upload to S3 for large data
        if len(json_data) > 1024 * 1024:  # 1MB threshold
            ss.upload(key, json_data.encode())
        else:
            # Use state store for smaller data
            st.set(key, json_data)

        # Update metadata
        metadata = {
            "last_sync": str(datetime.now()),
            "size": len(json_data),
            "source": "workflow",
        }
        st.set(f"{key}:metadata", json.dumps(metadata))
        return True
    except Exception as e:
        logger.error(f"Failed to upload to cloud: {e}")
        return False


# Expose undecorated implementation for test code
if hasattr(upload_to_cloud, "__wrapped__"):
    upload_to_cloud = cast(Callable[..., Any], upload_to_cloud.__wrapped__)


@wfr.workflow(name="cache_sync_wf")
def cache_sync_workflow(
    ctx: wf.DaprWorkflowContext, category: str, key: str, data: Optional[Dict[str, Any]] = None
) -> Generator[Any, None, WorkflowResponse]:
    """Run the cache sync workflow."""
    try:
        # If we have data to upload
        if data is not None:
            # Check if it already exists in cloud
            exists = yield ctx.call_activity(check_cloud_cache, input=key)
            if not exists:
                # Upload to cloud
                success = yield ctx.call_activity(upload_to_cloud, input=(key, data))
                if not success:
                    logger.error(f"Failed to upload {key} to cloud")
                    return {"success": False, "data": None, "error": "Upload failed"}
            return {"success": True, "data": data, "error": None}

        # If we're trying to get data
        else:
            # Try to download from cloud
            cloud_data = yield ctx.call_activity(download_from_cloud, input=key)
            if cloud_data:
                # Update local cache
                st = cast(DaprStateStore, state_store)
                st.set(key, json.dumps(cloud_data))
                return {"success": True, "data": cloud_data, "error": None}
            return {"success": False, "data": None, "error": "Data not found"}

    except Exception as e:
        logger.error(f"Cache sync workflow failed: {e}")
        return {"success": False, "data": None, "error": str(e)}

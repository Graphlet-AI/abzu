"""Cache sync service for Abzu pipeline."""

import json
import logging
import os
from typing import Any

from dapr.ext.fastapi import DaprApp
from fastapi import FastAPI
from pydantic import BaseModel

from abzu.utils import DaprS3Storage, DaprStateStore

app = FastAPI()
dapr_app = DaprApp(app)

logger = logging.getLogger(__name__)


class CloudEvent(BaseModel):
    """Cloud event model for Dapr pub/sub."""

    datacontenttype: str
    source: str
    topic: str
    pubsubname: str
    data: dict[str, Any]
    id: str
    specversion: str
    tracestate: str
    type: str
    traceid: str


class SyncEntry(BaseModel):
    """Sync entry model for cache sync events."""

    category: str
    key: str
    data: dict[str, Any]
    timestamp: str


@dapr_app.subscribe(pubsub="cachepubsub", topic="cache-sync")
async def handle_sync_event(event: CloudEvent) -> dict[str, bool]:
    """Handle cache sync events."""
    try:
        sync_entry = SyncEntry(**event.data)
        logger.info(f"Processing sync event for {sync_entry.category}:{sync_entry.key}")

        # Initialize Dapr clients
        state_store = DaprStateStore()
        s3_storage = DaprS3Storage()

        # Handle different categories
        if sync_entry.category == "kg":
            # Knowledge graphs go to S3
            s3_storage.upload(sync_entry.key, json.dumps(sync_entry.data).encode())
        elif sync_entry.category == "articles":
            # Articles go to state store
            state_store.set(sync_entry.key, json.dumps(sync_entry.data))
        elif sync_entry.category == "urls":
            # URLs go to state store
            state_store.set(sync_entry.key, json.dumps(sync_entry.data))
        elif sync_entry.category == "financial":
            # Financial data goes to state store
            state_store.set(sync_entry.key, json.dumps(sync_entry.data))
        else:
            logger.warning(f"Unknown category: {sync_entry.category}")

        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to process sync event: {e}")
        return {"success": False}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "6002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

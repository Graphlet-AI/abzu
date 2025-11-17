"""Utility functions for Abzu."""

import json
import os
import shutil
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

import pandas as pd

from abzu.logs import get_logger

logger = get_logger(__name__)

# --- Hybrid Cache Mode Utilities ---

CACHE_MODE_NONE = "none"
CACHE_MODE_LOCAL = "local"
CACHE_MODE_HYBRID = "hybrid"


def get_cache_mode() -> str:
    """Get the cache mode from the environment."""
    return os.environ.get("ABZU_CACHE_MODE", CACHE_MODE_NONE).lower()


# --- S3 Types ---
class S3Object(TypedDict):
    Key: str
    LastModified: Any
    ETag: str
    Size: int
    StorageClass: str


class S3ListResponse(TypedDict):
    Contents: List[S3Object]
    IsTruncated: bool
    KeyCount: int
    MaxKeys: int
    Name: str
    Prefix: str


# --- Dapr Types ---
class StateResponse(TypedDict):
    """Response type for state operations."""

    data: bytes
    etag: str


class StateItem(TypedDict):
    """Type for state items in bulk operations."""

    key: str
    value: str
    etag: Optional[str]
    metadata: Optional[Dict[str, str]]
    options: Optional[Dict[str, str]]  # For consistency and concurrency options


class StateOptions(TypedDict, total=False):
    """Options for state operations."""

    consistency: Optional[str]  # "strong" or "eventual"
    concurrency: Optional[str]  # "first-write" or "last-write"


class QueryFilter(TypedDict, total=False):
    """Type for query filters."""

    EQ: Dict[str, Any]
    NEQ: Dict[str, Any]
    GT: Dict[str, Any]
    GTE: Dict[str, Any]
    LT: Dict[str, Any]
    LTE: Dict[str, Any]
    IN: Dict[str, List[Any]]
    AND: List["QueryFilter"]
    OR: List["QueryFilter"]


class SortOrder(TypedDict):
    """Type for sort orders."""

    key: str
    order: Optional[str]  # "ASC" or "DESC"


class QueryPage(TypedDict, total=False):
    """Type for query pagination."""

    limit: int
    token: Optional[str]


class QueryRequest(TypedDict, total=False):
    """Type for query requests."""

    filter: QueryFilter
    sort: List[SortOrder]
    page: QueryPage


class QueryResult(TypedDict):
    """Type for query results."""

    key: str
    data: Dict[str, Any]
    etag: str


class QueryResponse(TypedDict):
    """Type for query responses."""

    results: List[QueryResult]
    token: Optional[str]


# --- Dapr Integration (for hybrid mode) ---
try:
    import boto3
    from botocore.config import Config
    from dapr.clients import DaprClient
    from dapr.clients.grpc._request import (
        TransactionalStateOperation,
        TransactionOperationType,
    )
    from dapr.clients.grpc._state import StateItem as DaprStateItem
    from dapr.clients.grpc._state import StateOptions as DaprStateOptions

    DAPR_AVAILABLE = True
except ImportError:
    DAPR_AVAILABLE = False


T = TypeVar("T")


def ensure_str(value: Optional[str], default: str) -> str:
    """Ensure a value is a string, using default if None."""
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value)}")
    return value


class DaprStateStore:
    """Dapr state store client for hybrid cache mode."""

    def __init__(self, store_name: Optional[str] = None):
        if not DAPR_AVAILABLE:
            raise ImportError("dapr Python SDK is not installed.")
        self.store_name = ensure_str(store_name or os.environ.get("DAPR_STATE_STORE"), "statestore")
        self.client = DaprClient()

    def get(
        self,
        key: str,
        metadata: Optional[Dict[str, str]] = None,
        options: Optional[DaprStateOptions] = None,
    ) -> Optional[str]:
        """Get state from Dapr state store.

        Args:
            key: The state key
            metadata: Optional metadata for the state operation
            options: Optional state options for consistency and concurrency

        Returns:
            Optional[str]: The state value as a string, or None if not found
        """
        try:
            result = self.client.get_state(self.store_name, key, state_metadata=metadata)
            if not result or not result.data:
                return None
            return cast(str, result.data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to get state for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: str,
        metadata: Optional[Dict[str, str]] = None,
        options: Optional[DaprStateOptions] = None,
        etag: Optional[str] = None,
    ) -> None:
        """Set state in Dapr state store.

        Args:
            key: The state key
            value: The state value as a string
            metadata: Optional metadata for the state operation
            options: Optional state options for consistency and concurrency
            etag: Optional ETag for first-write-wins concurrency
        """
        try:
            self.client.save_state(
                self.store_name, key, value, state_metadata=metadata, options=options, etag=etag
            )
        except Exception as e:
            logger.error(f"Failed to set state for key {key}: {e}")
            raise

    def delete(
        self,
        key: str,
        metadata: Optional[Dict[str, str]] = None,
        options: Optional[DaprStateOptions] = None,
        etag: Optional[str] = None,
    ) -> None:
        """Delete state from Dapr state store.

        Args:
            key: The state key to delete
            metadata: Optional metadata for the state operation
            options: Optional state options for consistency and concurrency
            etag: Optional ETag for first-write-wins concurrency
        """
        try:
            self.client.delete_state(
                self.store_name, key, state_metadata=metadata, options=options, etag=etag
            )
        except Exception as e:
            logger.error(f"Failed to delete state for key {key}: {e}")
            raise

    def get_bulk(
        self, keys: List[str], metadata: Optional[Dict[str, str]] = None
    ) -> List[StateItem]:
        """Get multiple states from Dapr state store.

        Args:
            keys: List of state keys to get
            metadata: Optional metadata for the state operation

        Returns:
            List[StateItem]: List of state items with their values
        """
        try:
            result = self.client.get_bulk_state(
                store_name=self.store_name, keys=keys, states_metadata=metadata
            ).items
            return [
                {
                    "key": item.key,
                    "value": (
                        item.data.decode() if isinstance(item.data, bytes) else str(item.data or "")
                    ),
                    "etag": item.etag,
                    "metadata": {},  # Dapr doesn't expose metadata in bulk get
                    "options": None,  # Dapr doesn't expose options in bulk get
                }
                for item in result
            ]
        except Exception as e:
            logger.error(f"Failed to get bulk states for keys {keys}: {e}")
            return []

    def set_bulk(self, states: List[StateItem]) -> None:
        """Set multiple states in Dapr state store.

        Args:
            states: List of state items to set
        """
        try:
            state_items = [
                DaprStateItem(key=item["key"], value=item["value"], etag=item.get("etag"))
                for item in states
            ]
            self.client.save_bulk_state(self.store_name, state_items)
        except Exception as e:
            logger.error(f"Failed to set bulk states: {e}")
            raise

    def execute_transaction(
        self, operations: List[Tuple[str, str, Optional[str], Optional[Dict[str, str]]]]
    ) -> None:
        """Execute a state transaction.

        Args:
            operations: List of (operation_type, key, value, metadata) tuples.
                      operation_type can be "upsert" or "delete"
        """
        try:
            transaction_ops = []
            for op_type, key, value, _ in operations:
                if op_type == "upsert":
                    transaction_ops.append(
                        TransactionalStateOperation(
                            operation_type=TransactionOperationType.upsert, key=key, data=value
                        )
                    )
                elif op_type == "delete":
                    transaction_ops.append(
                        TransactionalStateOperation(
                            operation_type=TransactionOperationType.delete, key=key
                        )
                    )

            self.client.execute_state_transaction(
                store_name=self.store_name, operations=transaction_ops
            )
        except Exception as e:
            logger.error(f"Failed to execute state transaction: {e}")
            raise

    def query(self, query: QueryRequest) -> QueryResponse:
        """Query state store using the Dapr query API.

        Args:
            query: The query request containing filter, sort, and pagination

        Returns:
            QueryResponse: The query results and pagination token

        Example:
            # Find all articles from a specific source
            result = state_store.query({
                "filter": {
                    "EQ": {"source": "news"}
                },
                "sort": [
                    {"key": "collected_at", "order": "DESC"}
                ],
                "page": {"limit": 10}
            })

            # Find articles in a date range
            result = state_store.query({
                "filter": {
                    "AND": [
                        {"GTE": {"collected_at": "2024-01-01"}},
                        {"LTE": {"collected_at": "2024-12-31"}}
                    ]
                }
            })
        """
        try:
            # Convert query to JSON string
            query_json = json.dumps(query)

            # Call Dapr query API
            response = self.client.query_state(store_name=self.store_name, query=query_json)

            # Parse response
            if not response or not response.results:
                return {"results": [], "token": None}

            return {
                "results": [
                    {
                        "key": item.key,
                        "data": (
                            json.loads(item.value.decode())
                            if isinstance(item.value, bytes)
                            else item.value
                        ),  # type: ignore[typeddict-item]
                        "etag": item.etag,
                    }
                    for item in response.results
                ],
                "token": response.token,
            }
        except Exception as e:
            logger.error(f"Failed to query state store: {e}")
            return {"results": [], "token": None}


class DaprS3Storage:
    """Dapr S3 binding client for hybrid cache mode."""

    def __init__(self, binding_name: Optional[str] = None):
        if not DAPR_AVAILABLE:
            raise ImportError("dapr Python SDK is not installed.")
        self.binding_name = ensure_str(
            binding_name or os.environ.get("DAPR_S3_BINDING"), "s3storage"
        )
        self.client = DaprClient()

        # Initialize S3 client for direct operations
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT", "http://minio:9000"),
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "minioadmin"),
            aws_secret_access_key=os.environ.get("S3_SECRET_KEY", "minioadmin"),
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket = os.environ.get("S3_BUCKET", "abzu-cache")

    def upload(self, s3_key: str, data: bytes) -> None:
        """Upload data to S3 using Dapr binding.

        Args:
            s3_key: The S3 object key
            data: The data to upload as bytes
        """
        metadata: Tuple[Tuple[str, str], ...] = (("key", s3_key),)
        self.client.invoke_binding(
            self.binding_name, operation="create", data=data, metadata=metadata
        )

    def download(self, s3_key: str) -> Optional[bytes]:
        """Download data from S3 using direct S3 client.

        Args:
            s3_key: The S3 object key

        Returns:
            Optional[bytes]: The downloaded data as bytes, or None if not found
        """
        try:
            # Try to get object from S3
            response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
            return cast(bytes, response["Body"].read())
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            return None

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys in the S3 bucket with optional prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List[str]: List of object keys
        """
        try:
            # Try Dapr binding first
            metadata: Tuple[Tuple[str, str], ...] = (("prefix", prefix),)
            response = self.client.invoke_binding(
                self.binding_name, operation="list", data=b"", metadata=metadata
            )
            if response.data:
                try:
                    return cast(List[str], json.loads(response.data.decode()))
                except json.JSONDecodeError:
                    logger.error("Failed to decode Dapr binding response")
                    return []

            # Fall back to direct S3 client
            s3_response = cast(
                S3ListResponse, self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            )
            contents = s3_response.get("Contents", [])
            return [obj["Key"] for obj in contents]
        except Exception as e:
            logger.error(f"Failed to list S3 keys: {e}")
            return []


# --- Example usage in your pipeline ---
#
# mode = get_cache_mode()
# if mode == CACHE_MODE_HYBRID:
#     state = DaprStateStore()
#     s3 = DaprS3Storage()
#     # Use state.get/set and s3.upload as needed
# elif mode == CACHE_MODE_LOCAL:
#     # Use local Redis or disk
# else:
#     # Use disk only


def backup_file(file_path: Union[str, Path]) -> bool:
    """
    Create a backup of a file if it exists.

    Args:
        file_path: Path to the file to backup

    Returns:
        bool: True if backup was created, False otherwise
    """
    path = Path(file_path)
    if not path.exists():
        return False

    backup_path = Path(f"{path}.bak")
    try:
        shutil.copy2(path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {path}: {e}")
        return False


def save_jsonl(
    data: list[dict[str, Any]] | pd.DataFrame,
    file_path: Union[str, Path],
    create_backup: bool = True,
) -> bool:
    """
    Save data to a JSONL file with backup option.

    Args:
        data: List of dictionaries or pandas DataFrame to save
        file_path: Path to save the file
        create_backup: Whether to create a backup of the file if it exists

    Returns:
        bool: True if successful, False otherwise
    """
    path = Path(file_path)

    # Create directory if it doesn't exist
    os.makedirs(path.parent, exist_ok=True)

    # Create backup if requested and file exists
    if create_backup:
        backup_file(path)

    try:
        if isinstance(data, pd.DataFrame):
            # Deep copy to avoid modifying original data
            data = data.copy()

            # Recursively convert any nested Pydantic models or non-dict objects to dicts
            def serialize_nested_objects(obj: Any) -> Any:
                """Recursively serialize nested objects to JSON-compatible dicts."""
                if hasattr(obj, "model_dump"):
                    # Pydantic model - convert to dict
                    return obj.model_dump(mode="json")
                elif hasattr(obj, "asDict"):
                    # PySpark Row - convert to dict
                    return obj.asDict()
                elif isinstance(obj, dict):
                    return {k: serialize_nested_objects(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [serialize_nested_objects(item) for item in obj]
                else:
                    return obj

            # Apply serialization to all columns that might contain nested objects
            for col in data.columns:
                if data[col].dtype == "object":  # Only process object columns
                    data[col] = data[col].apply(serialize_nested_objects)

            # Use pandas to_json with lines=True for JSONL format
            data.to_json(path, orient="records", lines=True, force_ascii=False)
        else:
            # Handle list of dictionaries
            with open(path, "w", encoding="utf-8") as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to save data to {path}: {e}")
        return False


def _get_existing_urls(file_path: Path) -> Set[str]:
    """Get set of existing URLs from JSONL file."""
    if not file_path.exists():
        return set()

    existing_urls = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if "url" in item:
                        existing_urls.add(item["url"])
                except (json.JSONDecodeError, Exception):
                    # Skip invalid lines
                    pass
    except Exception as e:
        logger.error(f"Error reading URLs from {file_path}: {e}")
    return existing_urls


def append_jsonl(
    data: dict[str, Any], file_path: Union[str, Path], create_backup: bool = True
) -> bool:
    """
    Append a record to a JSONL file with backup option.
    Prevents duplicate URLs from being added.

    Args:
        data: Dictionary to append
        file_path: Path to the file
        create_backup: Whether to create a backup of the file if it exists

    Returns:
        bool: True if successful, False otherwise
    """
    path = Path(file_path)
    os.makedirs(path.parent, exist_ok=True)

    if "url" in data and data["url"] in _get_existing_urls(path):
        logger.info(f"Skipping duplicate URL: {data['url']}")
        return True

    if create_backup and path.exists():
        backup_file(path)

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        logger.error(f"Failed to append data to {path}: {e}")
        return False


def load_jsonl(file_path: Union[str, Path]) -> list[dict[str, Any]]:
    """
    Load data from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of dictionaries loaded from the file
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {path}")
        return []

    data = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    data.append(item)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse line: {line}")
    except Exception as e:
        logger.error(f"Failed to load data from {path}: {e}")

    return data


def build_crawled_url_index(file_path: Union[str, Path]) -> set[str]:
    """
    Read a JSONL file and build an index of already crawled URLs.

    Args:
        file_path: Path to the JSONL file containing articles

    Returns:
        Set of URLs that have already been crawled
    """
    path = Path(file_path)
    crawled_urls: set[str] = set()

    if not path.exists():
        logger.info(f"No existing articles file found at {path}, starting fresh")
        return crawled_urls

    try:
        # Count entries for logging
        total_entries = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    if "url" in item:
                        crawled_urls.add(item["url"])
                    total_entries += 1
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line in {path}")
                except Exception as e:
                    logger.warning(f"Error processing line in {path}: {e}")
        logger.info(
            f"Loaded {len(crawled_urls)} unique URLs from {total_entries} entries in {path}"
        )
    except Exception as e:
        logger.error(f"Failed to build URL index from {path}: {e}")

    return crawled_urls


def deduplicate_articles(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deduplicate articles based on URL.

    Args:
        data: List of articles to deduplicate

    Returns:
        Deduplicated list of articles
    """
    if not data:
        return []

    # Use a dictionary to keep only the latest version of each article by URL
    unique_articles: dict[str, dict[str, Any]] = {}

    for article in data:
        if "url" in article:
            url = article["url"]
            # Keep this article if we haven't seen this URL before
            # Or if we have an existing article but this one is newer (based on collected_at)
            if url not in unique_articles or (
                "collected_at" in article
                and "collected_at" in unique_articles[url]
                and article["collected_at"] > unique_articles[url]["collected_at"]
            ):
                unique_articles[url] = article
        else:
            # Keep articles without URLs (though they should always have URLs)
            logger.warning("Found article without URL, keeping it anyway")
            # Use a random key for articles without URLs
            unique_articles[f"no_url_{len(unique_articles)}"] = article

    deduped_data = list(unique_articles.values())
    logger.info(f"Deduplicated {len(data)} articles to {len(deduped_data)} unique articles")
    return deduped_data

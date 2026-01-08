"""Semantic embedding-based entity resolution blocking using FAISS clustering.

Uses a subprocess-based approach to avoid PyTorch/FAISS memory conflicts on macOS.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.schemas import normalize_company_dataframe

logger = get_logger(__name__)


def _clean_none_values(obj: Any) -> Any:
    """Recursively remove None values from nested dicts to avoid Parquet VOID type.

    Parameters
    ----------
    obj : any
        The object to clean (dict, list, or scalar).

    Returns
    -------
    any
        Cleaned object with None values removed from dicts.
        Returns None if the entire object should be removed.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            cleaned_v = _clean_none_values(v)
            # Only include non-None values
            if cleaned_v is not None:
                cleaned[k] = cleaned_v
        # Return None if dict is empty after cleaning
        return cleaned if cleaned else None
    elif isinstance(obj, list):
        # Clean each element, keep non-None results
        cleaned_list = [_clean_none_values(item) for item in obj]
        return [item for item in cleaned_list if item is not None]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj


# Embedding subprocess script
EMBED_SCRIPT = """
import json
import sys
import numpy as np
from sentence_transformers import SentenceTransformer

# Read input
input_path = sys.argv[1]
output_path = sys.argv[2]
model_name = sys.argv[3]
batch_size = int(sys.argv[4])

with open(input_path, "r") as f:
    data = json.load(f)

names = data["names"]
print(f"Encoding {len(names)} company names with {model_name}...", file=sys.stderr)

model = SentenceTransformer(model_name, device="cpu")
embeddings = model.encode(names, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)

np.save(output_path, embeddings)
print(f"Saved embeddings with shape {embeddings.shape}", file=sys.stderr)
"""

# FAISS clustering subprocess script
FAISS_SCRIPT = """
import json
import sys
import numpy as np
import faiss

# Read input
embeddings_path = sys.argv[1]
uuids_path = sys.argv[2]
output_path = sys.argv[3]
target_block_size = int(sys.argv[4])
max_distance = float(sys.argv[5]) if sys.argv[5] != "None" else None

embeddings = np.load(embeddings_path).astype(np.float32)
embeddings = np.ascontiguousarray(embeddings)

with open(uuids_path, "r") as f:
    uuids = json.load(f)

n, d = embeddings.shape
print(f"Clustering {n} embeddings with {d} dimensions...", file=sys.stderr)

# Calculate nlist
nlist = max(1, n // target_block_size)
nlist = min(nlist, int(np.sqrt(n)))
nlist = max(nlist, 1)
print(f"Using nlist={nlist} clusters", file=sys.stderr)

# Create and train index
quantizer = faiss.IndexFlatIP(d)
index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)
index.train(embeddings)
index.add(embeddings)

# Get cluster assignments
distances, assignments = quantizer.search(embeddings, 1)
assignments = assignments.flatten()
distances = distances.flatten()

# Build blocks
blocks = {}
filtered_count = 0

for idx, (cluster_id, distance) in enumerate(zip(assignments, distances)):
    cosine_distance = 1 - distance
    if max_distance is not None and cosine_distance > max_distance:
        filtered_count += 1
        continue
    block_key = f"semantic_{cluster_id}"
    if block_key not in blocks:
        blocks[block_key] = []
    blocks[block_key].append(uuids[idx])

if filtered_count > 0:
    print(f"Filtered {filtered_count} companies exceeding max_distance", file=sys.stderr)

# Save results
with open(output_path, "w") as f:
    json.dump(blocks, f)

block_sizes = [len(v) for v in blocks.values()]
print(f"Created {len(blocks)} blocks", file=sys.stderr)
print(f"Block sizes: min={min(block_sizes)}, max={max(block_sizes)}, avg={np.mean(block_sizes):.1f}", file=sys.stderr)
"""


def _run_embedding_subprocess(
    names: list[str],
    model_name: str,
    batch_size: int,
    temp_dir: str,
) -> np.ndarray:
    """Run embedding generation in a subprocess.

    Parameters
    ----------
    names : list[str]
        List of company names to embed.
    model_name : str
        Name of the sentence-transformers model.
    batch_size : int
        Batch size for encoding.
    temp_dir : str
        Temporary directory for intermediate files.

    Returns
    -------
    np.ndarray
        Embedding matrix of shape (n, d).
    """
    input_path = os.path.join(temp_dir, "names.json")
    output_path = os.path.join(temp_dir, "embeddings.npy")

    # Write input
    with open(input_path, "w") as f:
        json.dump({"names": names}, f)

    # Run subprocess
    logger.info(f"Running embedding subprocess for {len(names):,} names...")
    result = subprocess.run(
        [sys.executable, "-c", EMBED_SCRIPT, input_path, output_path, model_name, str(batch_size)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"Embedding subprocess failed:\n{result.stderr}")
        raise RuntimeError(f"Embedding subprocess failed: {result.stderr}")

    logger.info(result.stderr.strip())

    # Load results
    embeddings = np.load(output_path)
    return embeddings


def _run_faiss_subprocess(
    embeddings: np.ndarray,
    uuids: list[str],
    target_block_size: int,
    max_distance: Optional[float],
    temp_dir: str,
) -> dict[str, list[str]]:
    """Run FAISS clustering in a subprocess.

    Parameters
    ----------
    embeddings : np.ndarray
        Embedding matrix of shape (n, d).
    uuids : list[str]
        List of company UUIDs.
    target_block_size : int
        Target average block size.
    max_distance : float, optional
        Maximum cosine distance threshold.
    temp_dir : str
        Temporary directory for intermediate files.

    Returns
    -------
    dict[str, list[str]]
        Dictionary mapping block_key to list of UUIDs.
    """
    embeddings_path = os.path.join(temp_dir, "embeddings.npy")
    uuids_path = os.path.join(temp_dir, "uuids.json")
    output_path = os.path.join(temp_dir, "blocks.json")

    # Write input
    np.save(embeddings_path, embeddings)
    with open(uuids_path, "w") as f:
        json.dump(uuids, f)

    # Run subprocess
    logger.info("Running FAISS clustering subprocess...")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            FAISS_SCRIPT,
            embeddings_path,
            uuids_path,
            output_path,
            str(target_block_size),
            str(max_distance),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"FAISS subprocess failed:\n{result.stderr}")
        raise RuntimeError(f"FAISS subprocess failed: {result.stderr}")

    logger.info(result.stderr.strip())

    # Load results
    with open(output_path, "r") as f:
        blocks = json.load(f)

    return blocks


def build_semantic_blocks(
    input_path: str = config.get("process.kg.er.paths.input"),
    output_path: str = config.get("process.kg.er.paths.names.blocks_dir"),
    target_block_size: int = 50,
    max_distance: Optional[float] = None,
    batch_size: int = 64,
    model_name: str = config.get("process.kg.er.model.blocker", "intfloat/multilingual-e5-base"),
    stop_spark: bool = True,
) -> None:
    """Build semantic blocks using FAISS IVF clustering on embeddings.

    Uses subprocess isolation to avoid PyTorch/FAISS memory conflicts on macOS.

    Parameters
    ----------
    input_path : str
        Path to the input companies parquet file.
    output_path : str
        Directory path to save output blocks.
    target_block_size : int, optional
        Target average number of companies per block, by default 50.
    max_distance : float, optional
        Maximum cosine distance threshold for clustering.
        Companies beyond this distance from centroids are filtered.
        Default is None (no filtering).
    batch_size : int, optional
        Batch size for embedding computation, by default 64.
    model_name : str, optional
        Name of the sentence-transformers model to use.
    stop_spark : bool, optional
        Whether to stop the Spark session after processing, by default True.
    """
    logger.info("=" * 60)
    logger.info("SEMANTIC BLOCKING WITH FAISS IVF CLUSTERING")
    logger.info("=" * 60)

    # Check if input file exists
    if not os.path.exists(input_path):
        error_msg = (
            f"Companies file or folder not found: {input_path}\n\n"
            f"The semantic blocking step requires company data.\n"
            f"Please ensure the input file exists."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Create output directory
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create SparkSession
    spark: SparkSession = get_spark_session(app_name="build_semantic_blocks")

    # Load companies
    logger.info(f"Loading companies from {input_path}")
    companies_df_raw = spark.read.parquet(input_path)

    # Normalize schema
    logger.info("Normalizing company schema...")
    companies_df = normalize_company_dataframe(companies_df_raw, preserve_extra_fields=False)

    total_companies = companies_df.count()
    logger.info(f"Loaded {total_companies:,} companies")

    # Convert to pandas for processing
    logger.info("Converting to pandas...")
    companies_pd = companies_df.toPandas()

    # Filter to companies with valid names and UUIDs
    valid_mask = (
        companies_pd["name"].notna()
        & (companies_pd["name"].str.strip() != "")
        & companies_pd["uuid"].notna()
    )
    valid_companies_pd = companies_pd[valid_mask].copy()

    valid_names = valid_companies_pd["name"].tolist()
    valid_uuids = valid_companies_pd["uuid"].tolist()

    logger.info(f"Found {len(valid_names):,} companies with valid names and UUIDs")
    if len(valid_names) < total_companies:
        logger.warning(
            f"Filtered out {total_companies - len(valid_names):,} companies with missing names/UUIDs"
        )

    if len(valid_names) == 0:
        logger.error("No valid companies to process!")
        if stop_spark:
            spark.stop()
        return

    # Use temporary directory for subprocess communication
    with tempfile.TemporaryDirectory() as temp_dir:
        # Phase 1: Generate embeddings in subprocess
        logger.info("Phase 1: Generating embeddings...")
        embeddings = _run_embedding_subprocess(valid_names, model_name, batch_size, temp_dir)
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")

        # Phase 2: Run FAISS clustering in subprocess
        logger.info("Phase 2: Running FAISS clustering...")
        blocks = _run_faiss_subprocess(
            embeddings, valid_uuids, target_block_size, max_distance, temp_dir
        )

    logger.info(f"Created {len(blocks):,} semantic blocks")

    # Build UUID to company data mapping
    uuid_to_company = valid_companies_pd.set_index("uuid").to_dict("index")

    # Convert blocks to DataFrame format
    logger.info("Converting blocks to DataFrame format...")
    rows = []
    for block_key, uuids in blocks.items():
        companies = []
        for uuid in uuids:
            if uuid in uuid_to_company:
                company_data = uuid_to_company[uuid].copy()
                company_data["uuid"] = uuid
                # Recursively clean None values from nested dicts to avoid VOID type in Parquet
                cleaned_data = _clean_none_values(company_data)
                if cleaned_data is not None:
                    companies.append(cleaned_data)

        rows.append(
            {
                "block_key": block_key,
                "block_key_type": "semantic",
                "companies": companies,
                "block_size": len(companies),
            }
        )

    blocks_pd = pd.DataFrame(rows)

    # Convert to Spark DataFrame and save
    logger.info("Converting to Spark DataFrame...")
    blocks_spark = spark.createDataFrame(blocks_pd)

    # Save semantic blocks
    semantic_blocks_path = os.path.join(output_path, "semantic_blocks.parquet")
    logger.info(f"Saving semantic blocks to {semantic_blocks_path}")
    blocks_spark.repartition(1).write.mode("overwrite").parquet(semantic_blocks_path)

    # Compute statistics
    block_sizes: list[int] = [len(uuids) for uuids in blocks.values()]
    singleton_count = sum(1 for s in block_sizes if s == 1)
    multi_company_count = sum(1 for s in block_sizes if s > 1)
    total_company_instances = sum(block_sizes)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SEMANTIC BLOCKING SUMMARY")
    logger.info("=" * 60)
    logger.info("WHAT IS SEMANTIC BLOCKING?")
    logger.info("  Uses E5-base embeddings + FAISS IVF clustering")
    logger.info("  Groups semantically similar company names together")
    logger.info("  Catches matches that name-based strategies miss")
    logger.info("")
    logger.info("INPUT DATA:")
    logger.info(f"  Total companies: {total_companies:,}")
    logger.info(f"  Companies with valid names: {len(valid_names):,}")
    logger.info(f"  Embedding dimensions: {embeddings.shape[1]}")
    logger.info("")
    logger.info("BLOCKING PARAMETERS:")
    logger.info(f"  Target block size: {target_block_size}")
    logger.info(f"  Model: {model_name}")
    if max_distance is not None:
        logger.info(f"  Max distance threshold: {max_distance}")
    logger.info("")
    logger.info("RESULTS:")
    logger.info(f"  Total blocks created: {len(blocks):,}")
    if len(blocks) > 0:
        logger.info(
            f"  Singleton blocks: {singleton_count:,} ({singleton_count / len(blocks) * 100:.1f}%)"
        )
        logger.info(
            f"  Multi-company blocks: {multi_company_count:,} "
            f"({multi_company_count / len(blocks) * 100:.1f}%)"
        )
        logger.info(f"  Average block size: {np.mean(block_sizes):.1f}")
        logger.info(f"  Min block size: {min(block_sizes)}")
        logger.info(f"  Max block size: {max(block_sizes)}")
    logger.info(f"  Total company instances: {total_company_instances:,}")
    logger.info("")
    logger.info("OUTPUT FILES:")
    logger.info(f"  Semantic blocks: {semantic_blocks_path}")
    logger.info("=" * 60)

    if stop_spark:
        spark.stop()


if __name__ == "__main__":
    build_semantic_blocks()

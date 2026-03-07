"""Semantic embedding-based entity resolution blocking using FAISS clustering.

Uses a subprocess-based approach to avoid PyTorch/FAISS memory conflicts on macOS.
"""

import json
import os
import subprocess
import sys
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyspark.sql.functions as F
from Levenshtein import distance as levenshtein_distance
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType

from abzu.config import config
from abzu.logs import get_logger
from abzu.spark.config import get_spark_session
from abzu.spark.schemas import (
    get_company_fields_without_blocks,
    normalize_company_dataframe,
)
from abzu.spark.utils import create_split_large_blocks_udtf

logger = get_logger(__name__)


def _compute_block_levenshtein_stats(names: list[str]) -> dict[str, Any]:
    """Compute Levenshtein distance statistics for a block of company names.

    Parameters
    ----------
    names : list[str]
        List of company names in the block.

    Returns
    -------
    dict[str, Any]
        Dictionary with Levenshtein distance statistics.
    """
    if len(names) <= 1:
        return {
            "unique_names": len(set(names)),
            "total_names": len(names),
            "min_lev": 0,
            "max_lev": 0,
            "mean_lev": 0.0,
            "exact_duplicates": len(names) - len(set(names)),
        }

    unique_names = list(set(names))
    if len(unique_names) <= 1:
        return {
            "unique_names": 1,
            "total_names": len(names),
            "min_lev": 0,
            "max_lev": 0,
            "mean_lev": 0.0,
            "exact_duplicates": len(names) - 1,
        }

    # Compute pairwise Levenshtein distances for unique names
    distances = []
    for name1, name2 in combinations(unique_names, 2):
        distances.append(levenshtein_distance(name1, name2))

    return {
        "unique_names": len(unique_names),
        "total_names": len(names),
        "min_lev": min(distances),
        "max_lev": max(distances),
        "mean_lev": float(np.mean(distances)),
        "exact_duplicates": len(names) - len(unique_names),
    }


def _compute_normalized_levenshtein(name1: str, name2: str) -> float:
    """Compute normalized Levenshtein distance (0-1 scale).

    Parameters
    ----------
    name1 : str
        First company name.
    name2 : str
        Second company name.

    Returns
    -------
    float
        Normalized Levenshtein distance (0 = identical, 1 = completely different).
    """
    if not name1 and not name2:
        return 0.0
    max_len = max(len(name1), len(name2))
    if max_len == 0:
        return 0.0
    return levenshtein_distance(name1, name2) / max_len


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
import torch
from sentence_transformers import SentenceTransformer

# Read input
input_path = sys.argv[1]
output_path = sys.argv[2]
model_name = sys.argv[3]
batch_size = int(sys.argv[4])

with open(input_path, "r") as f:
    data = json.load(f)

names = data["names"]

# Detect best available device
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
print(f"Encoding {len(names)} company names with {model_name} on {device}...", file=sys.stderr)

model = SentenceTransformer(model_name, device=device)
embeddings = model.encode(names, normalize_embeddings=True, batch_size=batch_size, show_progress_bar=True)

np.save(output_path, embeddings)
print(f"Saved embeddings with shape {embeddings.shape}", file=sys.stderr)
"""

# FAISS clustering subprocess script - returns detailed statistics for tuning
FAISS_SCRIPT = """
import json
import sys
import numpy as np
import faiss

# Read input
embeddings_path = sys.argv[1]
uuids_path = sys.argv[2]
output_path = sys.argv[3]
stats_path = sys.argv[4]
target_block_size = int(sys.argv[5])
max_distance = float(sys.argv[6]) if sys.argv[6] != "None" else None

embeddings = np.load(embeddings_path).astype(np.float32)
embeddings = np.ascontiguousarray(embeddings)

with open(uuids_path, "r") as f:
    uuids = json.load(f)

n, d = embeddings.shape
print(f"Clustering {n} embeddings with {d} dimensions...", file=sys.stderr)

# Calculate nlist (number of clusters = number of blocks)
nlist = max(1, n // target_block_size)
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

# Convert to cosine distances (1 - inner_product for normalized vectors)
cosine_distances = 1 - distances

# Compute distance statistics BEFORE filtering
distance_stats = {
    "min": float(np.min(cosine_distances)),
    "max": float(np.max(cosine_distances)),
    "mean": float(np.mean(cosine_distances)),
    "std": float(np.std(cosine_distances)),
    "p10": float(np.percentile(cosine_distances, 10)),
    "p25": float(np.percentile(cosine_distances, 25)),
    "p50": float(np.percentile(cosine_distances, 50)),
    "p75": float(np.percentile(cosine_distances, 75)),
    "p90": float(np.percentile(cosine_distances, 90)),
    "p95": float(np.percentile(cosine_distances, 95)),
    "p99": float(np.percentile(cosine_distances, 99)),
}

# Build blocks with distance tracking per block
blocks = {}
block_distances = {}  # Track distances per block for quality analysis
filtered_count = 0
filtered_distances = []

for idx, (cluster_id, cos_dist) in enumerate(zip(assignments, cosine_distances)):
    if max_distance is not None and cos_dist > max_distance:
        filtered_count += 1
        filtered_distances.append(cos_dist)
        continue
    block_key = f"semantic_{cluster_id}"
    if block_key not in blocks:
        blocks[block_key] = []
        block_distances[block_key] = []
    blocks[block_key].append(uuids[idx])
    block_distances[block_key].append(cos_dist)

# Compute per-block distance stats
block_quality = {}
for block_key, dists in block_distances.items():
    block_quality[block_key] = {
        "size": len(dists),
        "max_distance": float(max(dists)),
        "mean_distance": float(np.mean(dists)),
        "distance_spread": float(max(dists) - min(dists)) if len(dists) > 1 else 0.0,
    }

if filtered_count > 0:
    print(f"Filtered {filtered_count} companies exceeding max_distance={max_distance}", file=sys.stderr)
    distance_stats["filtered_count"] = filtered_count
    distance_stats["filtered_min"] = float(min(filtered_distances))
    distance_stats["filtered_max"] = float(max(filtered_distances))

# Save results
with open(output_path, "w") as f:
    json.dump(blocks, f)

# Save statistics
stats = {
    "distance_stats": distance_stats,
    "block_quality": block_quality,
    "nlist": nlist,
    "total_embeddings": n,
    "embedding_dim": d,
}
with open(stats_path, "w") as f:
    json.dump(stats, f)

block_sizes = [len(v) for v in blocks.values()]
if block_sizes:
    print(f"Created {len(blocks)} blocks", file=sys.stderr)
    print(f"Block sizes: min={min(block_sizes)}, max={max(block_sizes)}, avg={np.mean(block_sizes):.1f}", file=sys.stderr)
else:
    print("No blocks created (all filtered out)", file=sys.stderr)
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
    max_distance: float | None,
    temp_dir: str,
) -> tuple[dict[str, list[str]], dict[str, Any]]:
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
    tuple[dict[str, list[str]], dict[str, Any]]
        Tuple of (blocks dict, clustering statistics dict).
    """
    embeddings_path = os.path.join(temp_dir, "embeddings.npy")
    uuids_path = os.path.join(temp_dir, "uuids.json")
    output_path = os.path.join(temp_dir, "blocks.json")
    stats_path = os.path.join(temp_dir, "stats.json")

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
            stats_path,
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
    with open(output_path) as f:
        blocks = json.load(f)

    with open(stats_path) as f:
        stats = json.load(f)

    return blocks, stats


def build_semantic_blocks(
    input_path: str = config.get("process.kg.er.paths.input"),
    output_path: str = config.get("process.kg.er.paths.names.blocks_dir"),
    target_block_size: int = 50,
    max_distance: float | None = None,
    batch_size: int = 64,
    model_name: str = config.get("process.kg.er.model.blocker", "intfloat/multilingual-e5-base"),
    stop_spark: bool = True,
    iteration: int = 1,
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
    iteration : int, optional
        Current ER iteration number, by default 1.
        On later iterations the target block size is automatically scaled down
        to produce smaller, more focused clusters.
    """
    logger.info("=" * 60)
    logger.info("SEMANTIC BLOCKING WITH FAISS IVF CLUSTERING")
    logger.info("=" * 60)

    # ----------------------------------------------------------------
    # AUTO-SCALING: On later iterations the dataset has already been
    # deduplicated, so we shrink the FAISS target to produce smaller,
    # more focused clusters.  The formula divides the user-supplied
    # target_block_size by the iteration number (floored, min 10).
    #
    #   Iteration 1  -m 100  ->  effective_target = 100
    #   Iteration 2  -m 100  ->  effective_target =  50
    #   Iteration 3  -m 100  ->  effective_target =  33
    #
    # The effective target controls BOTH the FAISS nlist parameter
    # (number of Voronoi cells / clusters) AND the block-splitting
    # threshold that caps the maximum block size in the output.
    # ----------------------------------------------------------------
    effective_target = max(10, target_block_size // iteration)
    logger.info(
        f"Auto-scaled target block size: {target_block_size} / iteration {iteration}"
        f" = {effective_target}"
    )

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

    # Build UUID to name mapping for Levenshtein analysis
    uuid_to_name = dict(zip(valid_uuids, valid_names))

    # Use temporary directory for subprocess communication
    with tempfile.TemporaryDirectory() as temp_dir:
        # Phase 1: Generate embeddings in subprocess
        logger.info("Phase 1: Generating embeddings...")
        embeddings = _run_embedding_subprocess(valid_names, model_name, batch_size, temp_dir)
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")

        # Phase 2: Run FAISS clustering in subprocess
        logger.info("Phase 2: Running FAISS clustering...")
        blocks, clustering_stats = _run_faiss_subprocess(
            embeddings, valid_uuids, effective_target, max_distance, temp_dir
        )

    logger.info(f"Created {len(blocks):,} semantic blocks")

    # Phase 3: Compute Levenshtein distance statistics for each block
    logger.info("Phase 3: Computing Levenshtein distance statistics...")
    block_levenshtein_stats: dict[str, dict[str, Any]] = {}
    block_names: dict[str, list[str]] = {}

    for block_key, block_uuids in blocks.items():
        names_in_block = [uuid_to_name[u] for u in block_uuids if u in uuid_to_name]
        block_names[block_key] = names_in_block
        block_levenshtein_stats[block_key] = _compute_block_levenshtein_stats(names_in_block)

    # Build blocks in Spark using the same canonical struct as er_block.py
    # This ensures the companies struct schema is identical across blocking methods
    logger.info("Building blocks DataFrame in Spark...")

    # Create a mapping DataFrame: block_key -> uuid
    block_assignment_rows = []
    for block_key, block_uuids in blocks.items():
        for uuid_val in block_uuids:
            block_assignment_rows.append((block_key, "semantic", uuid_val))

    # Add singleton blocks for invalid companies (missing name/UUID)
    invalid_companies = companies_pd[~valid_mask]
    if len(invalid_companies) > 0:
        logger.warning(
            f"Creating {len(invalid_companies)} singleton blocks for companies "
            f"with missing names/UUIDs"
        )
        for _, row in invalid_companies.iterrows():
            company_uuid = row.get("uuid", "unknown")
            block_assignment_rows.append(
                (f"unblocked_{company_uuid}", "unblocked", str(company_uuid))
            )

    block_assignments_df = spark.createDataFrame(
        block_assignment_rows, schema="block_key string, block_key_type string, uuid string"
    )

    # Join with the normalized company DataFrame to get full company data
    blocks_with_companies = block_assignments_df.join(companies_df, "uuid", how="inner")

    # Build the company struct using the same canonical fields as er_block.py
    company_fields = get_company_fields_without_blocks()
    company_struct = F.struct(
        *[
            F.col(f) if f in blocks_with_companies.columns else F.lit(None).alias(f)
            for f in company_fields
        ]
    )

    # Group by block_key and collect companies into arrays
    blocks_spark = (
        blocks_with_companies.groupBy("block_key", "block_key_type")
        .agg(
            F.collect_list(company_struct).alias("companies"),
            F.countDistinct("uuid").alias("block_size"),
        )
        .select("block_key", "block_key_type", "companies", "block_size")
    )

    # Split large blocks into smaller chunks using the shared UDTF
    blocks_before_split = blocks_spark.count()
    oversized_before = blocks_spark.filter(F.col("block_size") > effective_target).count()

    if oversized_before > 0:
        logger.info(
            f"Splitting {oversized_before} blocks exceeding max size of {effective_target}..."
        )

        # Build UDTF return type from the DataFrame schema
        companies_field = blocks_spark.schema["companies"]
        companies_array_type = companies_field.dataType
        assert isinstance(companies_array_type, ArrayType), "companies must be an ArrayType"
        companies_schema = companies_array_type.elementType.simpleString()
        udtf_return_type = (
            f"block_key: string, block_key_type: string, "
            f"companies: array<{companies_schema}>, "
            f"block_size: long"
        )

        SplitLargeBlocks = create_split_large_blocks_udtf(udtf_return_type, effective_target)
        spark.udtf.register("split_large_blocks", SplitLargeBlocks)  # type: ignore[arg-type]

        blocks_spark.createOrReplaceTempView("semantic_blocks_temp")
        blocks_spark = spark.sql("""
            SELECT udtf_output.* FROM semantic_blocks_temp,
            LATERAL split_large_blocks(block_key, block_key_type, companies, block_size)
            AS udtf_output
            """)

        blocks_after_split = blocks_spark.count()
        new_blocks = blocks_after_split - blocks_before_split
        logger.info(
            f"Block splitting: {blocks_before_split} -> {blocks_after_split} "
            f"(+{new_blocks} sub-blocks from {oversized_before} oversized blocks)"
        )
    else:
        logger.info(f"No blocks exceed max size of {effective_target}, no splitting needed")

    # Save to semantic_blocks.parquet only (don't overwrite union_blocks.parquet from name blocking)
    semantic_blocks_path = os.path.join(output_path, "semantic_blocks.parquet")
    logger.info(f"Saving semantic blocks to {semantic_blocks_path}")
    blocks_spark.repartition(1).write.mode("overwrite").parquet(semantic_blocks_path)

    # Compute statistics from pre-split FAISS clusters
    pre_split_sizes: list[int] = [len(block_uuids) for block_uuids in blocks.values()]

    # Compute post-split statistics from the final Spark DataFrame
    final_stats = blocks_spark.agg(
        F.count("*").alias("total_blocks"),
        F.sum(F.when(F.col("block_size") == 1, 1).otherwise(0)).alias("singleton_count"),
        F.sum(F.when(F.col("block_size") > 1, 1).otherwise(0)).alias("multi_company_count"),
        F.sum("block_size").alias("total_instances"),
        F.min("block_size").alias("min_size"),
        F.max("block_size").alias("max_size"),
        F.avg("block_size").alias("mean_size"),
    ).collect()[0]

    singleton_count = int(final_stats["singleton_count"])
    multi_company_count = int(final_stats["multi_company_count"])
    total_company_instances = int(final_stats["total_instances"])
    total_final_blocks = int(final_stats["total_blocks"])

    # Get distance statistics from clustering
    dist_stats = clustering_stats.get("distance_stats", {})

    # Aggregate Levenshtein stats across all blocks
    all_max_lev = [s["max_lev"] for s in block_levenshtein_stats.values() if s["unique_names"] > 1]
    all_mean_lev = [
        s["mean_lev"] for s in block_levenshtein_stats.values() if s["unique_names"] > 1
    ]
    total_exact_duplicates = sum(s["exact_duplicates"] for s in block_levenshtein_stats.values())
    blocks_with_diversity = sum(
        1 for s in block_levenshtein_stats.values() if s["unique_names"] > 1
    )

    # Print comprehensive summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("SEMANTIC BLOCKING ANALYSIS REPORT")
    logger.info("=" * 80)

    # Section 1: Input Data
    logger.info("")
    logger.info("1. INPUT DATA")
    logger.info("-" * 40)
    logger.info(f"   Total company records:     {total_companies:,}")
    logger.info(f"   Valid records (with name): {len(valid_names):,}")
    logger.info(f"   Unique company names:      {len(set(valid_names)):,}")
    dup_rate = (1 - len(set(valid_names)) / len(valid_names)) * 100
    logger.info(f"   Duplicate rate:            {dup_rate:.1f}%")
    logger.info(f"   Embedding dimensions:      {embeddings.shape[1]}")

    # Section 2: Clustering Parameters
    logger.info("")
    logger.info("2. CLUSTERING PARAMETERS")
    logger.info("-" * 40)
    logger.info(f"   Model:             {model_name}")
    logger.info(
        f"   Target block size: {target_block_size}"
        f" (effective: {effective_target}, iteration {iteration})"
    )
    logger.info(f"   Actual nlist:      {clustering_stats.get('nlist', 'N/A')}")
    logger.info(
        f"   Max distance:      {max_distance if max_distance is not None else 'None (no filtering)'}"
    )

    # Section 3: Cosine Distance Distribution
    logger.info("")
    logger.info("3. COSINE DISTANCE DISTRIBUTION (to cluster centroid)")
    logger.info("-" * 40)
    logger.info("   Lower values = closer to centroid = tighter clusters")
    logger.info("")
    logger.info(f"   Min:         {dist_stats.get('min', 0):.6f}")
    logger.info(f"   10th %ile:   {dist_stats.get('p10', 0):.6f}")
    logger.info(f"   25th %ile:   {dist_stats.get('p25', 0):.6f}")
    logger.info(f"   Median:      {dist_stats.get('p50', 0):.6f}")
    logger.info(
        f"   Mean:        {dist_stats.get('mean', 0):.6f} (+/- {dist_stats.get('std', 0):.6f})"
    )
    logger.info(f"   75th %ile:   {dist_stats.get('p75', 0):.6f}")
    logger.info(f"   90th %ile:   {dist_stats.get('p90', 0):.6f}")
    logger.info(f"   95th %ile:   {dist_stats.get('p95', 0):.6f}")
    logger.info(f"   99th %ile:   {dist_stats.get('p99', 0):.6f}")
    logger.info(f"   Max:         {dist_stats.get('max', 0):.6f}")

    if "filtered_count" in dist_stats:
        logger.info("")
        logger.info(f"   FILTERED OUT: {dist_stats['filtered_count']:,} companies")
        logger.info(
            f"   (distances {dist_stats.get('filtered_min', 0):.4f} - {dist_stats.get('filtered_max', 0):.4f})"
        )

    # Section 4: Block Size Distribution
    logger.info("")
    logger.info("4. BLOCK SIZE DISTRIBUTION")
    logger.info("-" * 40)
    if len(blocks) > 0:
        logger.info("   Pre-split (FAISS clusters):")
        logger.info(f"     Total blocks:      {len(blocks):,}")
        logger.info(f"     Min size:          {min(pre_split_sizes)}")
        logger.info(f"     Max size:          {max(pre_split_sizes)}")
        logger.info(f"     Mean size:         {np.mean(pre_split_sizes):.1f}")
        logger.info(f"     Median size:       {np.median(pre_split_sizes):.1f}")
        oversized = sum(1 for s in pre_split_sizes if s > effective_target)
        if oversized > 0:
            logger.info(f"     Oversized (>{effective_target}): {oversized}")
        logger.info("")
        logger.info("   Post-split (final output):")
        logger.info(f"     Total blocks:      {total_final_blocks:,}")
        singleton_pct = singleton_count / total_final_blocks * 100
        multi_pct = multi_company_count / total_final_blocks * 100
        logger.info(f"     Singleton blocks:  {singleton_count:,} ({singleton_pct:.1f}%)")
        logger.info(f"     Multi-company:     {multi_company_count:,} ({multi_pct:.1f}%)")
        logger.info(f"     Max size:          {int(final_stats['max_size'])}")
        logger.info(f"     Mean size:         {final_stats['mean_size']:.1f}")
        logger.info(f"     Total instances:   {total_company_instances:,}")

    # Section 5: Levenshtein Distance Analysis
    logger.info("")
    logger.info("5. LEVENSHTEIN DISTANCE ANALYSIS")
    logger.info("-" * 40)
    logger.info(f"   Blocks with diverse names: {blocks_with_diversity:,} / {len(blocks):,}")
    logger.info(f"   Exact duplicates: {total_exact_duplicates:,}")
    if all_max_lev:
        logger.info(f"   Max Levenshtein:  {max(all_max_lev)} | Mean: {np.mean(all_mean_lev):.1f}")

    # Section 6: Sample Blocks (sorted by diversity/quality issues)
    logger.info("")
    logger.info("6. SAMPLE BLOCKS (sorted by Levenshtein distance - highest first)")
    logger.info("-" * 40)

    # Sort blocks by max Levenshtein distance (highest first = most problematic)
    sorted_blocks = sorted(
        [(k, v, block_levenshtein_stats[k]) for k, v in block_names.items()],
        key=lambda x: (x[2]["max_lev"], -x[2]["unique_names"]),
        reverse=True,
    )

    # Show top 5 most diverse blocks
    shown = 0
    for block_key, names, lev_stats in sorted_blocks[:10]:
        if lev_stats["unique_names"] <= 1:
            continue  # Skip blocks with only one unique name

        shown += 1
        if shown > 5:
            break

        unique = sorted(set(names))
        name_counts = {name: names.count(name) for name in unique}
        logger.info("")
        logger.info(f"   Block: {block_key}")
        logger.info(
            f"   Size: {lev_stats['total_names']} | Unique: {lev_stats['unique_names']} | Lev max: {lev_stats['max_lev']}"
        )
        logger.info("   Names (alphabetical):")
        for i, name in enumerate(unique[:10]):
            count = name_counts[name]
            logger.info(f"     {i + 1}. {name:<50} (x{count})")
        if len(unique) > 10:
            logger.info(f"     ... and {len(unique) - 10} more unique names")

    # Section 7: Recommendations
    logger.info("")
    logger.info("7. RECOMMENDATIONS")
    logger.info("-" * 40)

    # Analyze and provide recommendations
    if max_distance is None:
        logger.info("   [!] No max_distance set - all companies included regardless of cluster fit")
        logger.info(
            f"       Suggested: --max-distance {dist_stats.get('p75', 0.1):.4f} (75th percentile)"
        )
        logger.info(f"       Aggressive: --max-distance {dist_stats.get('p50', 0.05):.4f} (median)")

    if all_max_lev and max(all_max_lev) > 20:
        logger.info("")
        logger.info("   [!] High Levenshtein distances detected (>20 character edits)")
        logger.info("       This suggests semantically unrelated names in same cluster")
        logger.info("       Try: Lower --max-distance or increase --target-block-size")

    if blocks_with_diversity < len(blocks) * 0.1:
        logger.info("")
        logger.info("   [!] Most blocks contain only exact duplicates")
        logger.info("       Semantic blocking may not add value over deduplication")
        logger.info("       Try: Higher --max-distance to catch more semantic matches")

    avg_pre_split_size = np.mean(pre_split_sizes) if pre_split_sizes else 0
    if avg_pre_split_size > effective_target * 2:
        logger.info("")
        logger.info(
            f"   [!] Pre-split avg block size ({avg_pre_split_size:.0f}) >> target ({effective_target})"
        )
        logger.info("       Clusters are larger than expected")
        logger.info("       Try: Lower --max-distance or lower --target-block-size")

    if "filtered_count" in dist_stats and dist_stats["filtered_count"] > len(valid_names) * 0.5:
        logger.info("")
        filtered_pct = dist_stats["filtered_count"] / len(valid_names) * 100
        logger.info(f"   [!] Filtering removed {filtered_pct:.0f}% of companies")
        logger.info("       max_distance may be too restrictive")
        logger.info(
            f"       Try: --max-distance {dist_stats.get('p90', 0.2):.4f} (90th percentile)"
        )

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"OUTPUT: {semantic_blocks_path}")
    logger.info("=" * 80)

    if stop_spark:
        spark.stop()


if __name__ == "__main__":
    build_semantic_blocks()

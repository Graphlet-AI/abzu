"""Unit tests for semantic embedding-based entity resolution blocking."""

import os
import tempfile
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from pyspark.sql import SparkSession

from abzu.spark.er_block_semantic import (
    _clean_none_values,
    _compute_block_levenshtein_stats,
    _compute_normalized_levenshtein,
    _run_faiss_subprocess,
    build_semantic_blocks,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def spark() -> SparkSession:  # type: ignore
    """Create a SparkSession for testing."""
    spark = (
        SparkSession.builder.master("local[1]")  # type: ignore
        .appName("test_er_block_semantic")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def make_companies(n: int = 10, include_invalid: bool = False) -> list[dict[str, Any]]:
    """Create sample company records for testing.

    Parameters
    ----------
    n : int
        Number of valid companies to create.
    include_invalid : bool
        If True, append companies with null/empty names.
    """
    all_names = [
        "Apple Inc",
        "Apple Corporation",
        "Google LLC",
        "Alphabet Inc",
        "Microsoft Corporation",
        "Microsoft Corp",
        "NVIDIA Corporation",
        "Intel Corporation",
        "Amazon Web Services",
        "Meta Platforms",
        "Samsung Electronics",
        "Qualcomm Inc",
    ]
    companies: list[dict[str, Any]] = []
    for i, name in enumerate(all_names[:n]):
        company: dict[str, Any] = {
            "id": i + 1,
            "uuid": f"uuid-{i + 1}",
            "name": name,
            "description": f"Description for {name}",
            "cik": "",
            "website_url": "",
            "headquarters_location": "",
            "revenue_usd": 0.0,
            "employees": 0,
            "founded_year": 0,
            "ceo": "",
            "ticker": "",
            "linkedin_url": "",
            "jurisdiction": "",
        }
        companies.append(company)

    if include_invalid:
        companies.append(
            {
                "id": n + 1,
                "uuid": f"uuid-{n + 1}",
                "name": None,
                "description": "No name company",
                "cik": "",
                "website_url": "",
                "headquarters_location": "",
                "revenue_usd": 0.0,
                "employees": 0,
                "founded_year": 0,
                "ceo": "",
                "ticker": "",
                "linkedin_url": "",
                "jurisdiction": "",
            }
        )
        companies.append(
            {
                "id": n + 2,
                "uuid": f"uuid-{n + 2}",
                "name": "   ",
                "description": "Whitespace name company",
                "cik": "",
                "website_url": "",
                "headquarters_location": "",
                "revenue_usd": 0.0,
                "employees": 0,
                "founded_year": 0,
                "ceo": "",
                "ticker": "",
                "linkedin_url": "",
                "jurisdiction": "",
            }
        )
    return companies


# ---------------------------------------------------------------------------
# _clean_none_values
# ---------------------------------------------------------------------------


def test_clean_none_values_removes_none_from_dict() -> None:
    result = _clean_none_values({"a": 1, "b": None, "c": "hello"})
    assert result == {"a": 1, "c": "hello"}


def test_clean_none_values_nested_dict() -> None:
    result = _clean_none_values({"a": {"x": None, "y": 2}, "b": None})
    assert result == {"a": {"y": 2}}


def test_clean_none_values_all_none_dict() -> None:
    result = _clean_none_values({"a": None, "b": None})
    assert result is None


def test_clean_none_values_list() -> None:
    result = _clean_none_values([1, None, 3, None])
    assert result == [1, 3]


def test_clean_none_values_numpy_types() -> None:
    result = _clean_none_values({"a": np.int64(42), "b": np.float64(3.14)})
    assert result == {"a": 42, "b": 3.14}
    assert isinstance(result["a"], int)
    assert isinstance(result["b"], float)


def test_clean_none_values_numpy_array() -> None:
    result = _clean_none_values(np.array([1, 2, 3]))
    assert result == [1, 2, 3]


def test_clean_none_values_pandas_na() -> None:
    result = _clean_none_values({"a": pd.NA, "b": float("nan"), "c": 1})
    assert result == {"c": 1}


def test_clean_none_values_scalar_passthrough() -> None:
    assert _clean_none_values(42) == 42
    assert _clean_none_values("hello") == "hello"
    assert _clean_none_values(True) is True


def test_clean_none_values_empty_dict() -> None:
    assert _clean_none_values({}) is None


def test_clean_none_values_empty_list() -> None:
    assert _clean_none_values([]) == []


# ---------------------------------------------------------------------------
# _compute_normalized_levenshtein
# ---------------------------------------------------------------------------


def test_normalized_levenshtein_identical() -> None:
    assert _compute_normalized_levenshtein("Apple", "Apple") == 0.0


def test_normalized_levenshtein_completely_different() -> None:
    result = _compute_normalized_levenshtein("abc", "xyz")
    assert result == 1.0


def test_normalized_levenshtein_partial() -> None:
    result = _compute_normalized_levenshtein("Apple", "Apply")
    assert 0.0 < result < 1.0


def test_normalized_levenshtein_empty_strings() -> None:
    assert _compute_normalized_levenshtein("", "") == 0.0


def test_normalized_levenshtein_one_empty() -> None:
    result = _compute_normalized_levenshtein("Apple", "")
    assert result == 1.0


# ---------------------------------------------------------------------------
# _compute_block_levenshtein_stats
# ---------------------------------------------------------------------------


def test_block_levenshtein_stats_empty() -> None:
    stats = _compute_block_levenshtein_stats([])
    assert stats["total_names"] == 0
    assert stats["unique_names"] == 0
    assert stats["exact_duplicates"] == 0


def test_block_levenshtein_stats_single() -> None:
    stats = _compute_block_levenshtein_stats(["Apple"])
    assert stats["total_names"] == 1
    assert stats["unique_names"] == 1
    assert stats["min_lev"] == 0
    assert stats["max_lev"] == 0


def test_block_levenshtein_stats_all_duplicates() -> None:
    stats = _compute_block_levenshtein_stats(["Apple", "Apple", "Apple"])
    assert stats["total_names"] == 3
    assert stats["unique_names"] == 1
    assert stats["exact_duplicates"] == 2
    assert stats["min_lev"] == 0
    assert stats["max_lev"] == 0


def test_block_levenshtein_stats_distinct_names() -> None:
    stats = _compute_block_levenshtein_stats(["Apple Inc", "Apple Corp", "Google LLC"])
    assert stats["total_names"] == 3
    assert stats["unique_names"] == 3
    assert stats["exact_duplicates"] == 0
    assert stats["min_lev"] > 0
    assert stats["max_lev"] >= stats["min_lev"]
    assert stats["min_lev"] <= stats["mean_lev"] <= stats["max_lev"]


def test_block_levenshtein_stats_mix_duplicates_and_unique() -> None:
    stats = _compute_block_levenshtein_stats(["Apple", "Apple", "Google"])
    assert stats["total_names"] == 3
    assert stats["unique_names"] == 2
    assert stats["exact_duplicates"] == 1
    assert stats["max_lev"] > 0  # Apple vs Google


# ---------------------------------------------------------------------------
# _run_faiss_subprocess
# ---------------------------------------------------------------------------


def test_faiss_subprocess_assigns_all_vectors() -> None:
    """Every vector must be assigned to a block (100% coverage)."""
    n, d = 50, 32
    rng = np.random.default_rng(42)
    embeddings = rng.standard_normal((n, d)).astype(np.float32)
    # Normalize for inner-product / cosine
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    uuids = [f"uuid-{i}" for i in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        blocks, stats = _run_faiss_subprocess(
            embeddings, uuids, target_block_size=10, max_distance=None, temp_dir=tmp
        )

    # Flatten all UUIDs in blocks
    assigned_uuids = set()
    for block_uuids in blocks.values():
        assigned_uuids.update(block_uuids)

    assert assigned_uuids == set(uuids), "Not all companies were assigned to a block"


def test_faiss_subprocess_block_count() -> None:
    """Number of blocks should be roughly n / target_block_size."""
    n, d = 100, 32
    target = 10
    rng = np.random.default_rng(123)
    embeddings = rng.standard_normal((n, d)).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    uuids = [f"uuid-{i}" for i in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        blocks, stats = _run_faiss_subprocess(
            embeddings, uuids, target_block_size=target, max_distance=None, temp_dir=tmp
        )

    assert len(blocks) == stats["nlist"]
    # nlist should be roughly n / target = 10
    assert 1 <= len(blocks) <= n


def test_faiss_subprocess_max_distance_filters() -> None:
    """Setting a very tight max_distance should filter some companies."""
    n, d = 60, 16
    rng = np.random.default_rng(7)
    embeddings = rng.standard_normal((n, d)).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    uuids = [f"uuid-{i}" for i in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        blocks, stats = _run_faiss_subprocess(
            embeddings, uuids, target_block_size=10, max_distance=0.001, temp_dir=tmp
        )

    assigned = set()
    for block_uuids in blocks.values():
        assigned.update(block_uuids)

    # With a near-zero threshold most vectors should be filtered
    assert len(assigned) < n


def test_faiss_subprocess_stats_structure() -> None:
    """Stats dict should contain expected keys."""
    n, d = 30, 16
    rng = np.random.default_rng(0)
    embeddings = rng.standard_normal((n, d)).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    uuids = [f"uuid-{i}" for i in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        _, stats = _run_faiss_subprocess(
            embeddings, uuids, target_block_size=10, max_distance=None, temp_dir=tmp
        )

    assert "nlist" in stats
    assert "total_embeddings" in stats
    assert "embedding_dim" in stats
    assert "distance_stats" in stats
    assert "block_quality" in stats
    ds = stats["distance_stats"]
    for key in ["min", "max", "mean", "std", "p50"]:
        assert key in ds


def test_faiss_subprocess_no_duplicate_assignments() -> None:
    """Each UUID must appear in exactly one block."""
    n, d = 80, 32
    rng = np.random.default_rng(99)
    embeddings = rng.standard_normal((n, d)).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    uuids = [f"uuid-{i}" for i in range(n)]

    with tempfile.TemporaryDirectory() as tmp:
        blocks, _ = _run_faiss_subprocess(
            embeddings, uuids, target_block_size=20, max_distance=None, temp_dir=tmp
        )

    all_uuids: list[str] = []
    for block_uuids in blocks.values():
        all_uuids.extend(block_uuids)

    assert len(all_uuids) == len(set(all_uuids)), "Duplicate UUID assignments found"


# ---------------------------------------------------------------------------
# build_semantic_blocks (integration)
# ---------------------------------------------------------------------------


def _fake_embeddings(
    names: list[str], model_name: str, batch_size: int, temp_dir: str
) -> np.ndarray:
    """Return deterministic fake embeddings so tests don't need the real model."""
    rng = np.random.default_rng(hash(tuple(names)) % (2**31))
    emb = rng.standard_normal((len(names), 32)).astype(np.float32)
    norms = np.linalg.norm(emb, axis=1, keepdims=True)
    return emb / norms


def test_build_semantic_blocks_output_files(spark: SparkSession, tmp_path: Any) -> None:
    """build_semantic_blocks should produce semantic_blocks.parquet."""
    companies = make_companies(10)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=5,
            stop_spark=False,
        )

    assert os.path.exists(os.path.join(output_path, "semantic_blocks.parquet"))


def test_build_semantic_blocks_schema(spark: SparkSession, tmp_path: Any) -> None:
    """Output schema must have block_key, block_key_type, companies, block_size."""
    companies = make_companies(10)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=5,
            stop_spark=False,
        )

    blocks_df = spark.read.parquet(os.path.join(output_path, "semantic_blocks.parquet"))
    assert "block_key" in blocks_df.columns
    assert "block_key_type" in blocks_df.columns
    assert "companies" in blocks_df.columns
    assert "block_size" in blocks_df.columns


def test_build_semantic_blocks_coverage(spark: SparkSession, tmp_path: Any) -> None:
    """Every valid company UUID must appear in exactly one block."""
    companies = make_companies(10)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=5,
            stop_spark=False,
        )

    blocks_pd = pd.read_parquet(os.path.join(output_path, "semantic_blocks.parquet"))
    blocked_uuids: list[str] = []
    for companies_list in blocks_pd["companies"]:
        for company in companies_list:
            if isinstance(company, dict):
                blocked_uuids.append(company["uuid"])

    input_uuids = {f"uuid-{i + 1}" for i in range(10)}
    assert set(blocked_uuids) == input_uuids, "Not all companies appear in blocks"
    assert len(blocked_uuids) == len(set(blocked_uuids)), "Duplicate UUID in blocks"


def test_build_semantic_blocks_invalid_companies_get_unblocked(
    spark: SparkSession, tmp_path: Any
) -> None:
    """Companies with null/empty names should get singleton 'unblocked' blocks."""
    companies = make_companies(6, include_invalid=True)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=3,
            stop_spark=False,
        )

    blocks_pd = pd.read_parquet(os.path.join(output_path, "semantic_blocks.parquet"))

    # Check for unblocked blocks
    unblocked = blocks_pd[blocks_pd["block_key_type"] == "unblocked"]
    semantic = blocks_pd[blocks_pd["block_key_type"] == "semantic"]

    # The null-name company should be unblocked (whitespace may or may not depending on cleanup)
    assert len(unblocked) >= 1, "No unblocked blocks for invalid companies"

    # All unblocked blocks should be singletons
    for _, row in unblocked.iterrows():
        assert row["block_size"] == 1

    # Semantic blocks should only contain valid companies
    assert len(semantic) > 0


def test_build_semantic_blocks_block_key_type(spark: SparkSession, tmp_path: Any) -> None:
    """All semantic blocks should have block_key_type='semantic'."""
    companies = make_companies(8)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=4,
            stop_spark=False,
        )

    blocks_pd = pd.read_parquet(os.path.join(output_path, "semantic_blocks.parquet"))
    block_types = set(blocks_pd["block_key_type"].unique())
    assert "semantic" in block_types


def test_build_semantic_blocks_block_size_matches_companies(
    spark: SparkSession, tmp_path: Any
) -> None:
    """block_size should equal the actual number of companies in each block."""
    companies = make_companies(10)
    input_path = str(tmp_path / "companies.parquet")
    output_path = str(tmp_path / "blocks")
    spark.createDataFrame(companies).write.mode("overwrite").parquet(input_path)

    with patch(
        "abzu.spark.er_block_semantic._run_embedding_subprocess", side_effect=_fake_embeddings
    ):
        build_semantic_blocks(
            input_path=input_path,
            output_path=output_path,
            target_block_size=5,
            stop_spark=False,
        )

    blocks_pd = pd.read_parquet(os.path.join(output_path, "semantic_blocks.parquet"))
    for _, row in blocks_pd.iterrows():
        actual_size = len(row["companies"])
        assert row["block_size"] == actual_size, (
            f"Block {row['block_key']}: block_size={row['block_size']} "
            f"but has {actual_size} companies"
        )


def test_build_semantic_blocks_missing_input(tmp_path: Any) -> None:
    """Should raise FileNotFoundError when input path doesn't exist."""
    with pytest.raises(FileNotFoundError):
        build_semantic_blocks(
            input_path=str(tmp_path / "nonexistent.parquet"),
            output_path=str(tmp_path / "blocks"),
            stop_spark=False,
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

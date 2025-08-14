import numpy as np
import pandas as pd
import pytest

from abzu.er.blocker import E5EntityBlocker


@pytest.fixture
def blocker():
    """Create a real blocker instance."""
    # Using a small model for faster tests
    return E5EntityBlocker(model_name="sentence-transformers/all-MiniLM-L6-v2")


@pytest.fixture
def company_names():
    """Test company names for Taiwan Semiconductor Manufacturing Company."""
    return [
        "TSM",
        "TSMC",
        "TSMC (TSM)",
        "Taiwan",
        "Taiwan Power Company",
        "Taiwan Semiconductor",
        "Taiwan Semiconductor Manufacturing",
        "Taiwan Semiconductor Manufacturing Co.",
        "Taiwan Semiconductor Manufacturing Co. Ltd.",
        "Taiwan Semiconductor Manufacturing Company",
        "Taiwan Semiconductor Manufacturing Company, Limited",
        "Taiwan Semiconductor Manufacturing Company, Limited (TSMC)",
        "Taiwan Semiconductor Manufacturing Company, Ltd.",
        "Taiwanese Semiconductor Manufacturing Company",
    ]


def test_encode_companies(blocker, company_names):
    """Test encoding of company names."""
    embeddings = blocker.encode_companies(company_names)

    # The MiniLM model produces 384-dim embeddings
    assert embeddings.shape == (14, 384)
    assert isinstance(embeddings, np.ndarray)
    # Check that embeddings are normalized (sentence-transformers normalizes by default)
    norms = np.linalg.norm(embeddings, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_calculate_similarity_matrix(blocker, company_names):
    """Test similarity matrix calculation."""
    similarity_matrix = blocker.calculate_similarity_matrix(company_names)

    # Check matrix properties
    assert similarity_matrix.shape == (14, 14)
    assert np.allclose(similarity_matrix, similarity_matrix.T)  # Symmetric
    assert np.allclose(np.diag(similarity_matrix), 1.0)  # Diagonal should be 1
    # Check valid range
    assert np.all(similarity_matrix >= -1.0) and np.all(similarity_matrix <= 1.0)


def test_create_blocks(blocker, company_names):
    """Test blocking functionality."""
    blocks = blocker.create_blocks(company_names, threshold=0.7)

    # Check that blocks were created
    assert isinstance(blocks, dict)
    assert len(blocks) > 0

    # Check that all companies are in some block
    all_companies_in_blocks = []
    for block_companies in blocks.values():
        all_companies_in_blocks.extend(block_companies)
    assert set(all_companies_in_blocks) == set(company_names)

    # Check that similar companies tend to be grouped together
    # Find blocks containing TSMC variations
    tsmc_blocks = []
    for block_id, companies in blocks.items():
        if any("TSMC" in company for company in companies):
            tsmc_blocks.append(block_id)

    # At least one block should contain TSMC variations
    assert len(tsmc_blocks) > 0


def test_find_similar_companies(blocker, company_names):
    """Test finding similar companies."""
    query = "TSMC"
    candidates = [c for c in company_names if c != query]

    results = blocker.find_similar_companies(query, candidates, top_k=5)

    assert len(results) == 5
    assert all("company" in r and "similarity" in r for r in results)

    # Check that results are sorted by similarity
    similarities = [r["similarity"] for r in results]
    assert similarities == sorted(similarities, reverse=True)

    # The most similar should have reasonable similarity score
    assert results[0]["similarity"] > 0.5


def test_find_duplicates(blocker, company_names):
    """Test duplicate detection."""
    # Use a lower threshold to find more potential duplicates
    duplicates_df = blocker.find_duplicates(company_names, threshold=0.85)

    assert isinstance(duplicates_df, pd.DataFrame)

    # Check columns exist
    if len(duplicates_df) > 0:
        assert set(duplicates_df.columns) == {"company1", "company2", "similarity"}
        # Check that similarities are above threshold
        assert all(duplicates_df["similarity"] >= 0.85)

        # Check that pairs are unique (no reverse duplicates)
        pairs = set()
        for _, row in duplicates_df.iterrows():
            pair = tuple(sorted([row["company1"], row["company2"]]))
            assert pair not in pairs
            pairs.add(pair)


def test_get_pairwise_similarity(blocker):
    """Test pairwise similarity calculation."""
    similarity = blocker.get_pairwise_similarity(
        "Taiwan Semiconductor Manufacturing Company", "Taiwan Semiconductor Manufacturing Co."
    )

    assert isinstance(similarity, (float, np.floating))
    assert 0.0 <= similarity <= 1.0
    # These two names should be very similar
    assert similarity > 0.8


def test_model_initialization():
    """Test that the model is initialized with correct parameters."""
    # Test default model
    blocker1 = E5EntityBlocker()
    assert hasattr(blocker1, "model")
    assert blocker1.model is not None

    # Test with custom model
    custom_model = "sentence-transformers/all-MiniLM-L6-v2"
    blocker2 = E5EntityBlocker(model_name=custom_model)
    assert hasattr(blocker2, "model")
    assert blocker2.model is not None


def test_empty_company_list(blocker):
    """Test handling of empty company list."""
    # Should handle empty lists gracefully
    embeddings = blocker.encode_companies([])
    assert embeddings.shape[0] == 0

    # Empty company list should be handled by create_blocks directly
    blocks = blocker.create_blocks([])
    assert blocks == {}

    # Test calculate_similarity_matrix with empty list
    similarity_matrix = blocker.calculate_similarity_matrix([])
    assert similarity_matrix.shape == (0, 0)


def test_single_company(blocker):
    """Test handling of single company."""
    # Test encoding single company
    embeddings = blocker.encode_companies(["TSMC"])
    assert embeddings.shape == (1, 384)  # MiniLM produces 384-dim embeddings

    similarity_matrix = blocker.calculate_similarity_matrix(["TSMC"])
    assert similarity_matrix.shape == (1, 1)
    assert np.isclose(similarity_matrix[0, 0], 1.0)

    # Single company should be in its own block
    blocks = blocker.create_blocks(["TSMC"])
    assert len(blocks) == 1
    assert list(blocks.values())[0] == ["TSMC"]


def test_find_similar_with_few_candidates(blocker):
    """Test finding similar companies with fewer candidates than requested."""
    query = "TSMC"
    candidates = ["Taiwan", "Apple Inc."]

    # Request more results than candidates
    results = blocker.find_similar_companies(query, candidates, top_k=5)

    # Should return only as many as available
    assert len(results) == 2
    assert all("company" in r and "similarity" in r for r in results)


def test_real_world_similarity(blocker):
    """Test with real-world company name variations."""
    # Test that Apple variations are similar
    apple_sim = blocker.get_pairwise_similarity("Apple Inc.", "Apple")
    assert apple_sim > 0.8

    # Test that Microsoft variations are similar
    ms_sim = blocker.get_pairwise_similarity("Microsoft Corporation", "Microsoft Corp.")
    assert ms_sim > 0.8

    # Test that different companies have lower similarity
    diff_sim = blocker.get_pairwise_similarity("Apple Inc.", "Microsoft Corporation")
    assert diff_sim < 0.7

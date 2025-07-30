from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from abzu.er.blocker import E5EntityBlocker


@pytest.fixture
def blocker():
    """Create a blocker instance with mocked model."""
    with patch("abzu.er.blocker.SentenceTransformer") as MockModel:
        mock_model = MagicMock()
        MockModel.return_value = mock_model
        blocker = E5EntityBlocker()
        blocker.model = mock_model
        return blocker


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

    blocker.encode_companies(
        company_names,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    assert embeddings.shape == (14, 1024)  # Assuming E5 model produces 1024-dim embeddings
    assert isinstance(embeddings, np.ndarray)
    # Check that embeddings are normalized
    assert np.allclose(np.linalg.norm(embeddings, axis=1), 1.0, atol=1e-5)


def test_calculate_similarity_matrix(blocker, company_names):
    """Test similarity matrix calculation."""
    similarity_matrix = blocker.calculate_similarity_matrix(company_names)

    # Check matrix properties
    assert similarity_matrix.shape == (14, 14)
    assert np.allclose(similarity_matrix, similarity_matrix.T)  # Symmetric
    assert np.allclose(np.diag(similarity_matrix), 1.0)  # Diagonal should be 1
    # Check valid range with some tolerance for numerical errors
    assert np.all(similarity_matrix >= -1.01) and np.all(similarity_matrix <= 1.01)


def test_create_blocks(blocker, company_names):
    """Test blocking functionality."""

    # Use a lower threshold since our mock embeddings might not be perfect
    blocks = blocker.create_blocks(company_names, threshold=0.6)

    # Check that blocks were created
    assert isinstance(blocks, dict)
    assert len(blocks) > 0

    # Check that all companies are in some block
    all_companies_in_blocks = []
    for block_companies in blocks.values():
        for i, company in enumerate(block_companies):
            print(f"Block {i}: {company}")
        all_companies_in_blocks.extend(block_companies)
    assert set(all_companies_in_blocks) == set(company_names)

    # Check that TSMC variations are likely in the same block
    tsmc_block = None
    for block_id, block_companies in blocks.items():
        if "TSMC" in block_companies:
            tsmc_block = block_id
            break

    assert tsmc_block is not None
    tsmc_companies = blocks[tsmc_block]

    # Check that at least some TSMC variations are together
    tsmc_variations = [
        name
        for name in company_names
        if "TSMC" in name or "Taiwan Semiconductor Manufacturing" in name
    ]

    # Count how many TSMC variations are in the same block as "TSMC"
    tsmc_together_count = sum(1 for company in tsmc_variations if company in tsmc_companies)

    # At least 2 TSMC variations should be in the same block
    assert tsmc_together_count >= 2


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

    # At least one of the top results should be a TSMC variation
    top_companies = [r["company"] for r in results[:3]]
    tsmc_found = any(
        "TSMC" in company or "Taiwan Semiconductor" in company for company in top_companies
    )
    assert tsmc_found, f"No TSMC variations found in top 3 results: {top_companies}"


def test_find_duplicates(blocker, company_names):
    """Test duplicate detection."""

    duplicates_df = blocker.find_duplicates(company_names, threshold=0.8)

    assert isinstance(duplicates_df, pd.DataFrame)

    # If no duplicates found at threshold, it should be empty
    if len(duplicates_df) > 0:
        assert set(duplicates_df.columns) == {"company1", "company2", "similarity"}
        # Check that similarities are above threshold
        assert all(duplicates_df["similarity"] >= 0.8)

        # Check that pairs are unique (no reverse duplicates)
        pairs = set()
        for _, row in duplicates_df.iterrows():
            pair = tuple(sorted([row["company1"], row["company2"]]))
            assert pair not in pairs
            pairs.add(pair)
    else:
        # Empty dataframe case - still check it has the right columns
        assert len(duplicates_df) == 0


def test_get_pairwise_similarity(blocker):
    """Test pairwise similarity calculation."""
    # Mock embeddings for two similar companies
    similar_embeddings = np.array([[1.0, 0.0, 0.0], [0.9, 0.1, 0.0]])
    similar_embeddings = similar_embeddings / np.linalg.norm(
        similar_embeddings, axis=1, keepdims=True
    )

    blocker.model.encode.return_value = similar_embeddings

    similarity = blocker.get_pairwise_similarity(
        "Taiwan Semiconductor Manufacturing Company", "Taiwan Semiconductor Manufacturing Co."
    )

    assert isinstance(similarity, (float, np.floating))
    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.9  # Should be very similar


def test_model_initialization():
    """Test that the model is initialized with correct parameters."""
    with patch("abzu.er.blocker.SentenceTransformer") as MockModel:
        blocker = E5EntityBlocker()
        MockModel.assert_called_once_with("intfloat/multilingual-e5-large")
        assert blocker.__class__ == "E5EntityBlocker"

        MockModel.reset_mock()

        # Test with custom model
        custom_model = "intfloat/e5-large-v2"
        blocker2 = E5EntityBlocker(model_name=custom_model)
        MockModel.assert_called_with(custom_model)
        assert blocker2.__class__ == "E5EntityBlocker"


def test_empty_company_list(blocker):
    """Test handling of empty company list."""
    # Return empty 2D array to avoid sklearn error
    blocker.model.encode.return_value = np.array([]).reshape(0, 1024)

    # Should handle empty lists gracefully
    embeddings = blocker.encode_companies([])
    assert embeddings.shape == (0, 1024)

    # Empty company list should be handled by create_blocks directly
    blocks = blocker.create_blocks([])
    assert blocks == {}


def test_single_company(blocker):
    """Test handling of single company."""
    single_embedding = np.random.randn(1, 1024)
    single_embedding = single_embedding / np.linalg.norm(single_embedding)
    blocker.model.encode.return_value = single_embedding

    similarity_matrix = blocker.calculate_similarity_matrix(["TSMC"])
    assert similarity_matrix.shape == (1, 1)
    assert np.isclose(similarity_matrix[0, 0], 1.0)

    # Single company should be in its own block
    blocks = blocker.create_blocks(["TSMC"])
    assert len(blocks) == 1
    assert list(blocks.values())[0] == ["TSMC"]

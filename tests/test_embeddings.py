"""Tests for semantic embedding-based entity resolution blocking."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from abzu.er.embeddings import CompanyEmbedder


class TestCompanyEmbedder:
    """Tests for CompanyEmbedder class."""

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_init_uses_correct_device(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that CompanyEmbedder initializes with the correct device."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")

        assert embedder.device == "cpu"
        mock_transformer.assert_called_once_with("test-model", device="cpu")

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_init_with_mps_device(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that CompanyEmbedder works with MPS device (Apple Silicon)."""
        mock_get_device.return_value = "mps"
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")

        assert embedder.device == "mps"
        mock_transformer.assert_called_once_with("test-model", device="mps")

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_init_with_cuda_device(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that CompanyEmbedder works with CUDA device."""
        mock_get_device.return_value = "cuda"
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")

        assert embedder.device == "cuda"
        mock_transformer.assert_called_once_with("test-model", device="cuda")

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_encode_returns_normalized_embeddings(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that encode returns normalized embedding vectors."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        # Simulate normalized embeddings (unit vectors)
        mock_embeddings = np.array([[0.6, 0.8, 0.0], [0.0, 0.6, 0.8], [0.8, 0.0, 0.6]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")
        names = ["Apple Inc.", "Microsoft Corporation", "Google LLC"]
        result = embedder.encode(names, show_progress=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 3)
        mock_model.encode.assert_called_once_with(
            names,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_encode_with_custom_batch_size(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that encode respects custom batch size."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.5, 0.5]])
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")
        embedder.encode(["Test Company"], batch_size=32, show_progress=False)

        mock_model.encode.assert_called_once_with(
            ["Test Company"],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_encode_empty_list(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that encode handles empty list input."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([]).reshape(0, 768)
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")
        result = embedder.encode([], show_progress=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == (0, 768)

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_encode_single_company(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that encode handles single company input."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")
        result = embedder.encode(["Single Company Inc."], show_progress=False)

        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 4)

    @patch("abzu.er.embeddings.SentenceTransformer")
    @patch("abzu.er.embeddings.get_torch_device")
    def test_encode_preserves_order(
        self, mock_get_device: MagicMock, mock_transformer: MagicMock
    ) -> None:
        """Test that encode preserves input order in output."""
        mock_get_device.return_value = "cpu"
        mock_model = MagicMock()
        # Each company gets a distinct embedding
        mock_embeddings = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
        mock_model.encode.return_value = mock_embeddings
        mock_transformer.return_value = mock_model

        embedder = CompanyEmbedder(model_name="test-model")
        names = ["First", "Second", "Third"]
        result = embedder.encode(names, show_progress=False)

        # Verify the model received names in order
        call_args = mock_model.encode.call_args
        assert call_args[0][0] == names
        assert result.shape[0] == len(names)


@pytest.mark.slow
class TestCompanyEmbedderIntegration:
    """Integration tests for CompanyEmbedder (requires model download)."""

    @pytest.fixture(scope="class")
    def embedder(self) -> CompanyEmbedder:
        """Create a real CompanyEmbedder instance shared across all tests in this class."""
        return CompanyEmbedder()

    def test_real_encoding_produces_correct_shape(self, embedder: CompanyEmbedder) -> None:
        """Test that real encoding produces correct embedding dimensions."""
        names = ["Apple Inc.", "Microsoft Corporation"]
        result = embedder.encode(names, show_progress=False)

        assert isinstance(result, np.ndarray)
        assert result.shape[0] == 2
        # E5-base model produces 768-dimensional embeddings
        assert result.shape[1] == 768

    def test_real_embeddings_are_normalized(self, embedder: CompanyEmbedder) -> None:
        """Test that real embeddings are unit vectors (normalized)."""
        names = ["Test Company LLC"]
        result = embedder.encode(names, show_progress=False)

        # Normalized vectors should have L2 norm of 1
        norm = np.linalg.norm(result[0])
        assert np.isclose(norm, 1.0, atol=1e-5)

    def test_similar_companies_have_similar_embeddings(self, embedder: CompanyEmbedder) -> None:
        """Test that semantically similar companies have higher similarity."""
        names = [
            "Apple Inc.",
            "Apple Computer",
            "Microsoft Corporation",
        ]
        embeddings = embedder.encode(names, show_progress=False)

        # Compute cosine similarities (dot product for normalized vectors)
        apple_apple_sim = np.dot(embeddings[0], embeddings[1])
        apple_microsoft_sim = np.dot(embeddings[0], embeddings[2])

        # Apple Inc. should be more similar to Apple Computer than to Microsoft
        assert apple_apple_sim > apple_microsoft_sim

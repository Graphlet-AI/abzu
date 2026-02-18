"""Semantic blocking using embeddings and KMeans clustering.

This module provides utilities for semantic entity resolution blocking:
- CompanyEmbedder: Encodes company names using E5-large-instruct embeddings
- FAISSBlocker: Creates blocks using KMeans clustering (name preserved for compatibility)
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from abzu.config import config
from abzu.logs import get_logger
from abzu.utils import get_torch_device

logger = get_logger(__name__)


class CompanyEmbedder:
    """Embedding utility for company names using E5-large-instruct.

    Uses the multilingual intfloat/multilingual-e5-base model by default. Embeddings are normalized
    for use with inner product similarity metrics.

    Attributes
    ----------
    MODEL_NAME : str
        The HuggingFace model identifier.

    Examples
    --------
    >>> embedder = CompanyEmbedder()
    >>> names = ["Apple Inc.", "Microsoft Corporation", "Alphabet Inc."]
    >>> embeddings = embedder.encode(names)
    >>> embeddings.shape
    (3, 768)
    """

    def __init__(self, model_name: str = config.get("process.kg.er.model.blocker", "intfloat/multilingual-e5-base")) -> None:
        """Initialize the embedder with the best available device."""
        self.device = get_torch_device()
        logger.info(f"Initializing CompanyEmbedder on device: {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device)
        logger.info(f"Loaded model: {model_name}")

    def encode(
        self,
        names: list[str],
        batch_size: int = 64,
        show_progress: bool = True,
    ) -> np.ndarray:
        """Encode company names to normalized embedding vectors.

        Parameters
        ----------
        names : list[str]
            List of company names to encode.
        batch_size : int, optional
            Batch size for encoding, by default 64.
        show_progress : bool, optional
            Whether to show progress bar, by default True.

        Returns
        -------
        np.ndarray
            Normalized embedding vectors of shape (n, embedding_dim).
            For multilingual-e5-base, embedding_dim is 768.
        """

        logger.info(f"Encoding {len(names):,} company names...")
        embeddings: np.ndarray = self.model.encode(
            names,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            batch_size=batch_size,
        )
        logger.info(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings

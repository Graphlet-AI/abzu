from typing import Optional

import faiss
import numpy as np


class FAISSBlocker:
    """FAISS IVF-based semantic blocking with controlled granularity."""

    def __init__(
        self,
        target_block_size: int = 50,
        max_distance: Optional[float] = None,
    ):
        self.target_block_size = target_block_size
        self.max_distance = max_distance

        # One or the other - cant have both block size limits and distance limit
        if self.max_distance and self.target_block_size:
            raise ValueError("Specify either max_distance or target_block_size, not both.")

    def create_blocks(
        self,
        embeddings: np.ndarray,
        company_uuids: list[str],
    ) -> dict[str, list[str]]:
        """Create blocks from embeddings using FAISS IVF clustering.

        Args:
            embeddings: Normalized embedding vectors (n x d)
            company_uuids: List of company UUIDs corresponding to embeddings

        Returns:
            Dict mapping block_key to list of company UUIDs
        """
        n = len(embeddings)
        d = embeddings.shape[1]

        # Calculate nlist based on target block size
        # Rule: nlist = n / target_block_size
        nlist = max(1, n // self.target_block_size)

        # FAISS recommendation: nlist shouldn't exceed sqrt(n) for small datasets
        nlist = min(nlist, int(np.sqrt(n)))
        nlist = max(nlist, 1)

        # Create IVF index with inner product (for normalized vectors)
        quantizer = faiss.IndexFlatIP(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)

        # Train and add vectors
        index.train(embeddings.astype(np.float32))
        index.add(embeddings.astype(np.float32))

        # Get cluster assignments for each vector
        _, assignments = quantizer.search(embeddings.astype(np.float32), 1)
        assignments = assignments.flatten()

        # Build blocks from cluster assignments
        blocks: dict[str, list[str]] = {}
        for idx, cluster_id in enumerate(assignments):
            block_key = f"semantic_{cluster_id}"
            if block_key not in blocks:
                blocks[block_key] = []
            blocks[block_key].append(company_uuids[idx])

        return blocks

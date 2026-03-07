"""FAISS-based semantic blocking for entity resolution.

Uses FAISS IndexIVFFlat to cluster embeddings into blocks for efficient
entity comparison during matching.
"""

import faiss
import numpy as np

from abzu.logs import get_logger

logger = get_logger(__name__)


class FAISSBlocker:
    """FAISS IVF-based semantic blocking with controlled granularity.

    Uses FAISS IndexIVFFlat to partition embedding vectors into Voronoi cells
    using k-means clustering. Each cluster becomes a block for entity resolution.

    Parameters
    ----------
    target_block_size : int, optional
        Target average number of companies per block. Controls nlist as
        nlist = n / target_block_size. Default is 50.
    max_distance : float, optional
        Maximum cosine distance threshold for cluster membership.
        If provided, entities beyond this distance from their cluster
        centroid will be filtered out. Default is None (no filtering).

    Examples
    --------
    >>> blocker = FAISSBlocker(target_block_size=50)
    >>> embeddings = np.random.randn(1000, 768).astype(np.float32)
    >>> uuids = [f"uuid_{i}" for i in range(1000)]
    >>> blocks = blocker.create_blocks(embeddings, uuids)
    >>> len(blocks)  # Approximately 1000 / 50 = 20 blocks
    """

    def __init__(
        self,
        target_block_size: int = 50,
        max_distance: float | None = None,
    ):
        """Initialize the FAISS blocker.

        Parameters
        ----------
        target_block_size : int
            Target average number of companies per block.
        max_distance : float, optional
            Maximum distance threshold for filtering.
        """
        self.target_block_size = target_block_size
        self.max_distance = max_distance

        logger.info(f"Initialized FAISSBlocker with target_block_size={target_block_size}")
        if max_distance is not None:
            logger.info(f"  max_distance={max_distance}")

    def create_blocks(
        self,
        embeddings: np.ndarray,
        company_uuids: list[str],
    ) -> dict[str, list[str]]:
        """Create blocks from embeddings using FAISS IVF clustering.

        Parameters
        ----------
        embeddings : np.ndarray
            Normalized embedding vectors of shape (n, d).
        company_uuids : list[str]
            List of company UUIDs corresponding to embeddings.

        Returns
        -------
        dict[str, list[str]]
            Dictionary mapping block_key to list of company UUIDs.
        """
        n = len(embeddings)
        d = embeddings.shape[1]

        logger.info(f"Creating blocks for {n:,} companies with {d}-dim embeddings")

        # Calculate nlist based on target block size
        nlist = max(1, n // self.target_block_size)

        # FAISS recommendation: nlist shouldn't exceed sqrt(n) for small datasets
        nlist = min(nlist, int(np.sqrt(n)))
        nlist = max(nlist, 1)

        logger.info(f"Using nlist={nlist} clusters (target avg size: {n // nlist})")

        # Create IVF index with inner product (for normalized vectors = cosine similarity)
        quantizer = faiss.IndexFlatIP(d)
        index = faiss.IndexIVFFlat(quantizer, d, nlist, faiss.METRIC_INNER_PRODUCT)

        # Train and add vectors
        embeddings_f32 = embeddings.astype(np.float32)
        logger.info("Training FAISS index...")
        index.train(embeddings_f32)
        logger.info("Adding vectors to index...")
        index.add(embeddings_f32)

        # Get cluster assignments for each vector
        logger.info("Computing cluster assignments...")
        distances, assignments = quantizer.search(embeddings_f32, 1)
        assignments = assignments.flatten()
        distances = distances.flatten()

        # Build blocks from cluster assignments
        blocks: dict[str, list[str]] = {}
        filtered_count = 0

        for idx, (cluster_id, distance) in enumerate(zip(assignments, distances)):
            # Convert inner product to cosine distance (for normalized vectors)
            cosine_distance = 1 - distance

            # Apply max_distance filter if specified
            if self.max_distance is not None and cosine_distance > self.max_distance:
                filtered_count += 1
                continue

            block_key = f"semantic_{cluster_id}"
            if block_key not in blocks:
                blocks[block_key] = []
            blocks[block_key].append(company_uuids[idx])

        if filtered_count > 0:
            logger.info(
                f"Filtered {filtered_count:,} companies exceeding max_distance={self.max_distance}"
            )

        # Compute statistics
        block_sizes = [len(v) for v in blocks.values()]
        logger.info(f"Created {len(blocks):,} blocks")
        logger.info(
            f"Block size stats: min={min(block_sizes)}, max={max(block_sizes)}, "
            f"avg={np.mean(block_sizes):.1f}, median={np.median(block_sizes):.1f}"
        )

        return blocks

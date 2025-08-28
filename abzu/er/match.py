"""Entity resolution matching module."""

from typing import Optional

from abzu.logs import get_logger

logger = get_logger(__name__)


def match_entities(
    blocks_path: str,
    output_path: str,
    local_mode: Optional[bool] = None,
) -> None:
    """
    Match entities within blocks using similarity metrics.

    Args:
        blocks_path: Path to the blocks parquet file
        output_path: Path to save the matched entities
        local_mode: Whether to run in local mode. If None, will be determined by environment
    """
    logger.info(f"Starting entity matching from {blocks_path}")
    logger.info(f"Output path: {output_path}")

    # TODO: Implement entity matching logic
    # 1. Load blocks from parquet
    # 2. For each block, compute pairwise similarity
    # 3. Filter pairs above threshold
    # 4. Create match graph
    # 5. Save results

    logger.warning("Entity matching not yet implemented")

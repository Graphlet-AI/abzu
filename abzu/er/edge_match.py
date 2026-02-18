"""Edge resolution matching using BAML async client.

Merges duplicate relationships between the same pair of resolved company nodes.
After node entity resolution, multiple edges of the same or related types may exist
between the same pair of nodes. This module processes edge blocks through an LLM
to intelligently merge them.
"""

import asyncio
from typing import Any

from tqdm import tqdm

from abzu.baml_client import b as baml_client
from abzu.baml_client.types import EdgeBlock, EdgeRelationshipInput
from abzu.logs import get_logger

logger = get_logger(__name__)


async def process_edge_block(
    block: dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Process a single edge block through BAML ResolveEdgeBlock.

    Parameters
    ----------
    block : dict[str, Any]
        Dictionary containing edge block data with src/dst info and relationships.
    semaphore : asyncio.Semaphore
        Asyncio semaphore for rate limiting.

    Returns
    -------
    dict[str, Any]
        Dictionary with merged relationships and metadata.
    """
    async with semaphore:
        try:
            # Build BAML input
            relationships = [
                EdgeRelationshipInput(
                    type=rel.get("relationship", rel.get("type", "Unknown")),
                    description=rel.get("description", ""),
                    amount=rel.get("amount"),
                    currency=rel.get("currency"),
                    date=rel.get("date"),
                    percentage=rel.get("percentage"),
                    quarter=rel.get("quarter"),
                    url=rel.get("url"),
                )
                for rel in block["relationships"]
            ]

            edge_block = EdgeBlock(
                src_name=block["src_name"],
                dst_name=block["dst_name"],
                relationships=relationships,
                block_size=block["block_size"],
            )

            result = await baml_client.ResolveEdgeBlock(edge_block)

            # Collect all source URLs from original relationships
            all_urls = []
            for rel in block["relationships"]:
                url = rel.get("url")
                if url and url not in all_urls:
                    all_urls.append(url)

            return {
                "src": block["src"],
                "dst": block["dst"],
                "src_name": block["src_name"],
                "dst_name": block["dst_name"],
                "merged_relationships": [
                    {
                        "relationship": mr.type,
                        "description": mr.description,
                        "amount": mr.amount,
                        "currency": mr.currency,
                        "date": mr.date,
                        "percentage": mr.percentage,
                        "quarter": mr.quarter,
                    }
                    for mr in result.merged_relationships
                ],
                "urls": all_urls,
                "was_resolved": result.was_resolved,
                "original_count": result.original_count,
                "resolved_count": result.resolved_count,
            }
        except Exception as e:
            logger.error(
                f"Error processing edge block "
                f"({block.get('src_name', '?')} -> {block.get('dst_name', '?')}): {e}"
            )
            # Return original relationships on error
            return {
                "src": block["src"],
                "dst": block["dst"],
                "src_name": block["src_name"],
                "dst_name": block["dst_name"],
                "merged_relationships": [
                    {
                        "relationship": rel.get("relationship", rel.get("type", "Unknown")),
                        "description": rel.get("description", ""),
                        "amount": rel.get("amount"),
                        "currency": rel.get("currency"),
                        "date": rel.get("date"),
                        "percentage": rel.get("percentage"),
                        "quarter": rel.get("quarter"),
                    }
                    for rel in block["relationships"]
                ],
                "urls": [rel.get("url") for rel in block["relationships"] if rel.get("url")],
                "was_resolved": False,
                "original_count": block["block_size"],
                "resolved_count": block["block_size"],
                "error": str(e),
            }


async def resolve_edge_blocks(
    blocks: list[dict[str, Any]],
    batch_size: int = 5,
) -> list[dict[str, Any]]:
    """Process all edge blocks with rate limiting.

    Parameters
    ----------
    blocks : list[dict[str, Any]]
        List of edge block dictionaries, each containing src/dst UUIDs,
        company names, and a list of relationships to merge.
    batch_size : int, optional
        Maximum number of concurrent API calls, by default 5.

    Returns
    -------
    list[dict[str, Any]]
        List of resolved edge block results.
    """
    semaphore = asyncio.Semaphore(batch_size)
    tasks = [process_edge_block(block, semaphore) for block in blocks]

    results: list[dict[str, Any]] = []
    pbar: Any
    with tqdm(total=len(tasks), desc="Resolving edge blocks") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            pbar.update(1)

    return results


def run_edge_resolution(
    blocks: list[dict[str, Any]],
    batch_size: int = 5,
) -> list[dict[str, Any]]:
    """Synchronous wrapper for edge resolution.

    Parameters
    ----------
    blocks : list[dict[str, Any]]
        List of edge block dictionaries.
    batch_size : int, optional
        Maximum number of concurrent API calls, by default 5.

    Returns
    -------
    list[dict[str, Any]]
        List of resolved edge block results.
    """
    return asyncio.run(resolve_edge_blocks(blocks, batch_size))

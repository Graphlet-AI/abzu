"""CLI command for refining knowledge graph."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "--iteration",
    type=int,
    default=config.get("process.kg.er.iteration", 3),
    help="ER iteration number to use for resolved companies.",
)
@click.option(
    "--wiki/--no-wiki",
    "enrich_wiki",
    default=False,
    help="Enrich companies with Wikipedia data after refinement.",
)
@click.option(
    "--wiki-batch-size",
    type=int,
    default=config.get("process.kg.wiki.concurrent", 5),
    help="Number of concurrent Wikipedia requests.",
)
@click.option(
    "--wiki-limit",
    type=int,
    default=None,
    help="Maximum number of companies to enrich with Wikipedia (for testing).",
)
@click.option(
    "--edge-er/--no-edge-er",
    "use_edge_er",
    default=False,
    help="Use LLM-based edge resolution instead of simple deduplication.",
)
@click.option(
    "--edge-er-batch-size",
    type=int,
    default=config.get("process.kg.refine.edge_er.batch_size", 5),
    help="Batch size for concurrent edge ER API calls.",
)
@click.option(
    "--edge-er-min-block-size",
    type=int,
    default=config.get("process.kg.refine.edge_er.min_block_size", 2),
    help="Minimum edges per (src, dst) pair to trigger edge ER.",
)
def refine(
    iteration: int,
    enrich_wiki: bool,
    wiki_batch_size: int,
    wiki_limit: int | None,
    use_edge_er: bool,
    edge_er_batch_size: int,
    edge_er_min_block_size: int,
) -> int:
    """Refine knowledge graph by mapping relationships to resolved companies.

    Optionally enriches companies with Wikipedia data using --wiki flag.
    Use --edge-er to enable LLM-based edge resolution for merging duplicate
    relationships between the same pair of resolved companies.
    """
    # Import heavy module only when command is executed
    from abzu.kg.processor import process_refine_kg

    # Manually resolve dict paths from config by getting each value individually
    input_paths = {
        "companies": config.get("process.kg.refine.input.companies"),
        "relationships": config.get("process.kg.refine.input.relationships"),
    }
    output_paths = {
        "nodes": config.get("process.kg.refine.output.nodes"),
        "edges": config.get("process.kg.refine.output.edges"),
    }

    return process_refine_kg(
        input_paths=input_paths,
        output_paths=output_paths,
        iteration=iteration,
        enrich_wiki=enrich_wiki,
        wiki_batch_size=wiki_batch_size,
        wiki_limit=wiki_limit,
        use_edge_er=use_edge_er,
        edge_er_batch_size=edge_er_batch_size,
        edge_er_min_block_size=edge_er_min_block_size,
    )

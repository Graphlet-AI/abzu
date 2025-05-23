"""CLI command for refining knowledge graph."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_dir",
    default="data/knowledge_graph",
    help="Input directory with raw knowledge graph (default: data/knowledge_graph)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="data/refined_knowledge_graph",
    help="Output directory for refined knowledge graph (default: data/refined_knowledge_graph)",
)
@click.option(
    "-p",
    "--partitions",
    type=int,
    default=4,
    help="Number of Spark partitions (default: 4)",
)
def refine(input_dir, output_dir, partitions):
    """Refine knowledge graph by creating bidirectional relationships."""
    from abzu.kg.processor import process_refine_kg

    return process_refine_kg(
        input_dir=input_dir,
        output_dir=output_dir,
        partitions=partitions,
    )

"""CLI command for extracting raw knowledge graph."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    default="data/processed_semianalysis.jsonl",
    help="Input processed articles JSONL file (default: data/processed_semianalysis.jsonl)",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="data/knowledge_graph",
    help="Output directory for knowledge graph (default: data/knowledge_graph)",
)
@click.option(
    "-p",
    "--partitions",
    type=int,
    default=4,
    help="Number of Spark partitions (default: 4)",
)
def raw(input_file, output_dir, partitions):
    """Extract raw knowledge graph from processed articles."""
    from abzu.kg.processor import process_raw_kg

    return process_raw_kg(
        input_file=input_file,
        output_dir=output_dir,
        partitions=partitions,
    )

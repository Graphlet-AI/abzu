"""CLI command for extracting raw knowledge graph."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    default=config.get("process.kg.raw.input"),
    help="Comma-separated input processed articles JSONL files",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default=config.get("process.kg.raw.output"),
    help=f"Output directory for knowledge graph (default: {config.get('process.kg.raw.output')})",
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

"""CLI command for refining knowledge graph."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_dir",
    default=config.get("process.kg.refine.input"),
    help=f"Input directory with raw knowledge graph (default: {config.get('process.kg.refine.input')})",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default=config.get("process.kg.refine.output"),
    help=f"Output directory for refined knowledge graph (default: {config.get('process.kg.refine.output')})",
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

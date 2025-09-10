"""CLI command for refining knowledge graph."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_dir",
    default=config.get("process.kg.refine.input"),
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Input directory with raw knowledge graph.",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default=config.get("process.kg.refine.output"),
    type=click.Path(file_okay=False, dir_okay=True),
    help="Output directory for refined knowledge graph.",
)
def refine(input_dir, output_dir):
    """Refine knowledge graph by creating bidirectional relationships."""
    # Import heavy module only when command is executed
    from abzu.kg.processor import process_refine_kg

    return process_refine_kg(
        input_dir=input_dir,
        output_dir=output_dir,
    )

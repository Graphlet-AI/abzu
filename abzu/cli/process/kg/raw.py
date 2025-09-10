"""CLI command for extracting raw knowledge graph."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    required=False,
    multiple=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
    default=config.get("process.kg.raw.input"),
    help="Comma-separated input processed articles JSONL files.",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default=config.get("process.kg.raw.output"),
    help="Output directory for raw knowledge graph type Parquet files.",
)
def raw(input_file, output_dir):
    """Extract raw knowledge graph from processed articles."""
    # Import heavy module only when command is executed
    from abzu.kg.processor import process_raw_kg

    return process_raw_kg(
        input_file=list(input_file),
        output_dir=output_dir,
    )

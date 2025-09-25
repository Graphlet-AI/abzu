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
@click.option(
    "--iteration",
    type=int,
    default=config.get("process.kg.er.iteration", 4),
    help="ER iteration number to use for resolved companies.",
)
def refine(input_dir: str, output_dir: str, iteration: int) -> int:
    """Refine knowledge graph by mapping relationships to resolved companies."""
    # Import heavy module only when command is executed
    from abzu.kg.processor import process_refine_kg

    # Convert directory paths to the expected dict format
    input_paths = {
        "companies": f"{input_dir}/companies.parquet",
        "relationships": f"{input_dir}/relationships.parquet",
    }
    output_paths = {
        "nodes": f"{output_dir}/nodes.parquet",
        "edges": f"{output_dir}/edges.parquet",
    }

    return process_refine_kg(
        input_paths=input_paths,
        output_paths=output_paths,
        iteration=iteration,
    )

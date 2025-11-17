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
def refine(iteration: int) -> int:
    """Refine knowledge graph by mapping relationships to resolved companies."""
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
    )

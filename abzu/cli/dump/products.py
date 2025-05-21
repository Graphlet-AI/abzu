"""CLI command to display company products."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--file",
    "input_file",
    default="data/refined_knowledge_graph/products.parquet",
    help="Path to Parquet file with product information",
)
def products(input_file: str) -> int:
    """Show company products from a Parquet file."""
    from abzu.dump.products import dump_products_main

    return dump_products_main(input_file)

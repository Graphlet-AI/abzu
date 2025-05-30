"""CLI command to display companies."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--file",
    "input_file",
    default="data/refined_knowledge_graph/companies.parquet",
    help="Path to Parquet file with company information",
)
def companies(input_file: str) -> int:
    """Show companies from a Parquet file."""
    from abzu.dump.companies import dump_companies_main

    return dump_companies_main(input_file)

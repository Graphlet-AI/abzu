"""CLI command to display and apply ticker matches."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--file",
    "input_file",
    default="data/refined_knowledge_graph/companies.parquet",
    help="Path to companies.parquet file",
)
def company_ticker_resolution(input_file: str) -> int:
    """Show proposed tickers for companies missing them.

    Any perfect match is written back to the file.
    """
    from abzu.dump.company_ticker_resolution import dump_company_ticker_resolution_main

    return dump_company_ticker_resolution_main(input_file)

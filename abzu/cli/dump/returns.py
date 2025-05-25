"""CLI command to display top performing stocks."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--file",
    "input_file",
    default="data/financialdatasets/all_prices.json",
    help="Path to JSON file created by 'abzu api financialdatasets price'",
)
def returns(input_file: str) -> int:
    """Show best performing stocks from a price history file."""
    from abzu.dump.returns import dump_returns_main

    return dump_returns_main(input_file)

"""CLI command to display top performing stocks."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-f",
    "--file",
    "input_file",
    default=config.get("dump.returns.input"),
    type=click.Path(exists=True, dir_okay=True, file_okay=True, path_type=str),
    help="Path to JSON file created by 'abzu api financialdatasets price'",
)
def returns(input_file: str) -> int:
    """Show best performing stocks from a price history file."""
    from abzu.dump.returns import dump_returns_main

    return dump_returns_main(input_file)

"""CLI for entity resolution blocking."""

import click

from .names import names


@click.group()
def block() -> None:
    """Build entity resolution blocks."""
    pass


block.add_command(names)

"""CLI for entity resolution matching."""

import click

from .names import names


@click.group()
def match() -> None:
    """Match entities within blocks using similarity metrics."""
    pass


match.add_command(names)

"""CLI for entity resolution evaluation."""

import click

from .names import names


@click.group()
def eval() -> None:
    """Evaluate entity resolution matches."""
    pass


eval.add_command(names)

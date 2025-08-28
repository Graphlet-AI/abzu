"""CLI commands for entity resolution processing."""

import click

from abzu.cli.process.er.block import block
from abzu.cli.process.er.match import match


@click.group()
def er():
    """Entity resolution commands."""
    pass


er.add_command(block)
er.add_command(match)

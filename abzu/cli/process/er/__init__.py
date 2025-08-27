"""CLI commands for entity resolution processing."""

import click

from abzu.cli.process.er.block import block


@click.group()
def er():
    """Entity resolution commands."""
    pass


er.add_command(block)

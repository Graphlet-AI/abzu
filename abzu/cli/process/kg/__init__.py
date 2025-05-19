"""CLI module for knowledge graph processing commands."""

import click

from abzu.cli.process.kg.raw import raw
from abzu.cli.process.kg.refine import refine


@click.group()
def kg():
    """Process articles into a knowledge graph."""
    pass


kg.add_command(raw)
kg.add_command(refine)

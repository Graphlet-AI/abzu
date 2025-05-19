"""CLI module for processing commands."""

import click

from abzu.cli.process.articles import articles
from abzu.cli.process.kg import kg


@click.group()
def process():
    """Process data for knowledge extraction."""
    pass


process.add_command(articles)
process.add_command(kg)

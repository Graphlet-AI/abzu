"""CLI module for processing commands."""

import click

from abzu.cli.process.articles import articles
from abzu.cli.process.er import er
from abzu.cli.process.kg import kg
from abzu.cli.process.rss import rss


@click.group()
def process():
    """Process data for knowledge extraction."""
    pass


process.add_command(articles)
process.add_command(er)
process.add_command(kg)
process.add_command(rss)

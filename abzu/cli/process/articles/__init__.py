"""CLI module for article processing commands."""

import click

from abzu.cli.process.articles.semianalysis import process_semianalysis


@click.group()
def articles():
    """Process articles through LLM extraction pipeline."""
    pass


articles.add_command(process_semianalysis, name="semianalysis")

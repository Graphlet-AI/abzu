"""CLI module for article processing commands."""

import click

from abzu.cli.process.articles.datacenter import process_datacenter
from abzu.cli.process.articles.semianalysis import process_semianalysis
from abzu.cli.process.articles.theinformation import process_theinformation


@click.group()
def articles():
    """Process articles through LLM extraction pipeline."""
    pass


articles.add_command(process_semianalysis, name="semianalysis")
articles.add_command(process_theinformation, name="theinformation")
articles.add_command(process_datacenter, name="datacenter")

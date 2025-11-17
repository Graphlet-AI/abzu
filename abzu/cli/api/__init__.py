"""CLI module for API commands."""

import click

from abzu.cli.api.financialdatasets import financialdatasets
from abzu.cli.api.sec import sec
from abzu.cli.api.wiki import wiki


@click.group()
def api() -> None:
    """API access to external data sources."""
    pass


api.add_command(financialdatasets)
api.add_command(sec)
api.add_command(wiki)

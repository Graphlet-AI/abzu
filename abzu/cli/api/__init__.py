"""CLI module for API commands."""

import click

from abzu.cli.api.financialdatasets import financialdatasets
from abzu.cli.api.sec import sec


@click.group()
def api():
    """API access to external data sources."""
    pass


api.add_command(financialdatasets)
api.add_command(sec)

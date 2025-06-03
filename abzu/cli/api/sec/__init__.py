"""CLI module for SEC API commands."""

import click

from abzu.cli.api.sec.annual_report import annual_report
from abzu.cli.api.sec.download import download


@click.group()
def sec():
    """SEC API access."""
    pass


sec.add_command(download)
sec.add_command(annual_report)

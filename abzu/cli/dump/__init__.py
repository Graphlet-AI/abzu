"""CLI group for dump commands."""

import click

from abzu.cli.dump.returns import returns


@click.group()
def dump() -> None:
    """Dump derived data from Abzu."""
    pass


dump.add_command(returns)

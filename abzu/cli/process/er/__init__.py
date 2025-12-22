"""CLI commands for entity resolution processing."""

import click

from abzu.cli.utils import OrderedLazyGroup


@click.command(
    cls=OrderedLazyGroup,
    lazy_subcommands={
        "all": "abzu.cli.process.er.all:all",
        "block": "abzu.cli.process.er.block:block",
        "match": "abzu.cli.process.er.match:match",
        "eval": "abzu.cli.process.er.eval:eval",
        "clean": "abzu.cli.process.er.clean:clean",
    },
)
def er() -> None:
    """Entity resolution commands."""
    pass

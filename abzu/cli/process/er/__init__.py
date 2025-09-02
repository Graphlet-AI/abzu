"""CLI commands for entity resolution processing."""

import click

from abzu.cli.process.er.block import block
from abzu.cli.process.er.eval import eval
from abzu.cli.process.er.match import match


class OrderedGroup(click.Group):
    """A Click group that preserves command order."""

    def list_commands(self, ctx):
        """Return commands in the order they were added."""
        return ["block", "match", "eval"]


@click.group(cls=OrderedGroup)
def er():
    """Entity resolution commands."""
    pass


er.add_command(block)
er.add_command(match)
er.add_command(eval)

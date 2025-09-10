"""CLI commands for entity resolution processing."""

import click


class OrderedLazyGroup(click.Group):
    """A Click group that preserves command order and loads commands lazily."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        """Return commands in the order they were added."""
        return ["block", "match", "eval", "clean"]

    def get_command(self, ctx, name):
        if name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=OrderedLazyGroup,
    lazy_subcommands={
        "block": "abzu.cli.process.er.block:block",
        "match": "abzu.cli.process.er.match:match",
        "eval": "abzu.cli.process.er.eval:eval",
        "clean": "abzu.cli.process.er.clean:clean",
    },
)
def er():
    """Entity resolution commands."""
    pass

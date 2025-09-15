"""CLI module for RSS processing commands."""

import click


class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx, name):
        if name in self.lazy_subcommands:
            import_path, cmd_name = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=LazyGroup,
    lazy_subcommands={
        "process": (
            "abzu.cli.process.rss.process:rss",
            "process",
        ),
        "clean": ("abzu.cli.process.rss.clean:clean", "clean"),
    },
)
def rss():
    """Process RSS feeds through LLM extraction pipeline."""
    pass

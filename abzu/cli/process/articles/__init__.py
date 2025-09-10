"""CLI module for article processing commands."""

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
        "semianalysis": (
            "abzu.cli.process.articles.semianalysis:process_semianalysis",
            "semianalysis",
        ),
        "theinformation": (
            "abzu.cli.process.articles.theinformation:process_theinformation",
            "theinformation",
        ),
        "datacenter": ("abzu.cli.process.articles.datacenter:process_datacenter", "datacenter"),
        "dcbyte": ("abzu.cli.process.articles.dcbyte:process_dcbyte", "dcbyte"),
        "reddit": ("abzu.cli.process.articles.reddit:process_reddit", "reddit"),
    },
)
def articles():
    """Process articles through LLM extraction pipeline."""
    pass

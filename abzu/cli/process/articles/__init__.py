"""CLI module for article processing commands."""

import click


class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(
        self, *args, lazy_subcommands: dict[str, str | tuple[str, str]] | None = None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str | tuple[str, str]] = lazy_subcommands or {}

    def list_commands(self, ctx):
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx, name):
        if name in self.lazy_subcommands:
            value = self.lazy_subcommands[name]
            if isinstance(value, tuple):
                import_path, _ = value
            else:
                import_path = value
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
        "clean": ("abzu.cli.process.articles.clean:clean", "clean"),
    },
)
def articles():
    """Process articles through LLM extraction pipeline."""
    pass

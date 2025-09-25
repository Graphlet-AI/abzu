"""CLI for entity resolution matching."""

import click


class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(self, *args, lazy_subcommands: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str] = lazy_subcommands or {}

    def list_commands(self, ctx):
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx, name):
        if name in self.lazy_subcommands:
            from . import names

            return names.names
        return None


@click.command(
    cls=LazyGroup,
    lazy_subcommands={
        "names": ".names:names",
    },
)
def match() -> None:
    """Match entities within blocks using similarity metrics."""
    pass

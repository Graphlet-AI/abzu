"""CLI module for knowledge graph processing commands."""

from typing import Any

import click


# Lazy loading group for kg subcommands
class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(
        self, *args: Any, lazy_subcommands: dict[str, str] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=LazyGroup,
    lazy_subcommands={
        "raw": "abzu.cli.process.kg.raw:raw",
        "refine": "abzu.cli.process.kg.refine:refine",
        "tickers": "abzu.cli.process.kg.tickers:tickers",
    },
)
def kg() -> None:
    """Process articles into a knowledge graph."""
    pass

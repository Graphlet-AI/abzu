"""CLI commands for entity resolution processing."""

from typing import Any

import click


class OrderedLazyGroup(click.Group):
    """A Click group that preserves command order and loads commands lazily."""

    def __init__(
        self, *args: Any, lazy_subcommands: dict[str, str] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Return commands in the order they were added."""
        return [
            "all",
            "block",
            "match",
            "eval",
            "clean",
            "stage",
        ]

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=OrderedLazyGroup,
    lazy_subcommands={
        "all": "abzu.cli.process.er.all:all",
        "block": "abzu.cli.process.er.block:block",
        "match": "abzu.cli.process.er.match:match",
        "eval": "abzu.cli.process.er.eval:eval",
        "clean": "abzu.cli.process.er.clean:clean",
        "stage": "abzu.cli.process.er.stage:stage",
    },
)
def er() -> None:
    """Entity resolution commands."""
    pass

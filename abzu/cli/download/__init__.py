"""CLI commands for downloading datasets."""

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
        return list(self.lazy_subcommands.keys())

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)  # type: ignore[no-any-return]
        return None


@click.command(
    cls=OrderedLazyGroup,
    lazy_subcommands={
        "walmart-amazon": "abzu.cli.download.walmart_amazon:walmart_amazon",
    },
)
def download() -> None:
    """Download and process external datasets."""
    pass

"""CLI module for RSS processing commands."""

from typing import Any

import click


class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(
        self,
        *args: Any,
        lazy_subcommands: dict[str, str | tuple[str, str]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str | tuple[str, str]] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self.lazy_subcommands:
            value = self.lazy_subcommands[cmd_name]
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
        "process": (
            "abzu.cli.process.rss.process:rss",
            "process",
        ),
        "clean": ("abzu.cli.process.rss.clean:clean", "clean"),
    },
)
def rss() -> None:
    """Process RSS feeds through LLM extraction pipeline."""
    pass

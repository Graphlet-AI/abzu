"""CLI tools for Abzu using Click."""

import sys

import click

from abzu.logs import get_logger

logger = get_logger(__name__)


class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx, name):
        if name in self.lazy_subcommands:
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=LazyGroup,
    lazy_subcommands={
        "api": "abzu.cli.api:api",
        "chat": "abzu.cli.chat:chat",
        "crawl": "abzu.cli.crawl:crawl",
        "data": "abzu.cli.data:data",
        "dump": "abzu.cli.dump:dump",
        "process": "abzu.cli.process:process",
        "steps": "abzu.cli.steps:steps",
    },
)
def cli():
    """Abzu - Industry knowledge extraction."""
    pass


def main() -> int:
    """Main entry point for the abzu command line interface."""
    # Click automatically exits with the return code
    return cli() or 0


if __name__ == "__main__":
    sys.exit(main())

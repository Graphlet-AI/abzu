"""CLI tools for Abzu using Click."""

import sys

import click

from abzu.cli.api import api
from abzu.cli.chat import chat
from abzu.cli.crawl import crawl
from abzu.cli.dump import dump
from abzu.cli.process import process
from abzu.cli.steps import steps
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group()
def cli():
    """Abzu - Industry knowledge extraction."""
    pass


# Register main commands
cli.add_command(api)
cli.add_command(chat)
cli.add_command(crawl)
cli.add_command(process)
cli.add_command(steps)
cli.add_command(dump)


def main() -> int:
    """Main entry point for the abzu command line interface."""
    # Click automatically exits with the return code
    return cli() or 0


if __name__ == "__main__":
    sys.exit(main())

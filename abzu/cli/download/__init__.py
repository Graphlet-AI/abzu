"""CLI commands for downloading datasets."""

import click

from abzu.cli.utils import OrderedLazyGroup


@click.command(
    cls=OrderedLazyGroup,
    lazy_subcommands={
        "walmart-amazon": "abzu.cli.download.walmart_amazon:walmart_amazon",
    },
)
def download() -> None:
    """Download and process external datasets."""
    pass

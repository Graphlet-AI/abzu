"""CLI group for dump commands."""

import click

from abzu.cli.dump.companies import companies
from abzu.cli.dump.company_ticker_resolution import company_ticker_resolution
from abzu.cli.dump.products import products
from abzu.cli.dump.returns import returns


@click.group()
def dump() -> None:
    """Dump derived data from Abzu."""
    pass


dump.add_command(returns)
dump.add_command(products)
dump.add_command(companies)
dump.add_command(company_ticker_resolution)

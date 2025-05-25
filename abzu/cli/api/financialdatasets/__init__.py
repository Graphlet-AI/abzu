"""CLI module for Financial Datasets API commands."""

import click

from abzu.cli.api.financialdatasets.facts import facts
from abzu.cli.api.financialdatasets.metrics import metrics
from abzu.cli.api.financialdatasets.price import price
from abzu.cli.api.financialdatasets.tickers import tickers


@click.group()
def financialdatasets():
    """Financial Datasets API access."""
    pass


financialdatasets.add_command(facts)
financialdatasets.add_command(price)
financialdatasets.add_command(metrics)
financialdatasets.add_command(tickers)

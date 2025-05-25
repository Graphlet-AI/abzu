"""CLI module for chat bot commands."""

import click

from abzu.cli.chat.auth import auth
from abzu.cli.chat.key import key
from abzu.cli.chat.start import start


@click.group()
def chat():
    """Chat bot for URL monitoring and article processing."""
    pass


chat.add_command(start)
chat.add_command(key)
chat.add_command(auth)

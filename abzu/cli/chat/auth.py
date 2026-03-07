"""CLI command for generating Discord bot authorization URLs."""

import os

import click

from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "-a",
    "--app-id",
    help="Discord application ID (defaults to DISCORD_APPLICATION_ID env var)",
)
@click.option(
    "-r",
    "--redirect-uri",
    help="Optional redirect URI after authorization",
)
def auth(app_id: str | None, redirect_uri: str | None) -> int:
    """Generate Discord bot authorization URL.

    This command generates a URL that can be used to add the bot to a Discord server.
    """
    from abzu.chat.bot import BotRunner

    app_id = app_id or os.environ.get("DISCORD_APPLICATION_ID")

    if not app_id:
        logger.error(
            "Discord application ID is required. Use --app-id or set DISCORD_APPLICATION_ID env var."
        )
        return 1

    try:
        # Create a temporary bot runner to generate the URL
        bot_runner = BotRunner(application_id=app_id, token="placeholder")
        auth_url = bot_runner.get_auth_url(redirect_uri)

        click.secho("\nDiscord Bot Authorization URL:", fg="green", bold=True)
        click.echo(auth_url)
        click.echo("\nUse this URL to add your bot to a Discord server.")
        click.echo("Required permissions value: 377957895232")
        return 0
    except Exception as e:
        click.secho(f"Error generating authorization URL: {e}", fg="red")
        return 1

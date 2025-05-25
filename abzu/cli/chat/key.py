"""CLI command for verifying Discord authentication tokens."""

import asyncio
import logging
import os
from typing import Optional

import click
from discord.errors import HTTPException, LoginFailure
from discord.http import HTTPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "-t",
    "--token",
    help="Discord bot token (defaults to DISCORD_BOT_TOKEN env var)",
)
def key(token: Optional[str]):
    """Verify Discord authentication token.

    This command performs a simple API call to verify that the Discord token is valid.
    """
    token = token or os.environ.get("DISCORD_BOT_TOKEN")

    if not token:
        logger.error("Discord bot token is required. Use --token or set DISCORD_BOT_TOKEN env var.")
        return 1

    logger.info("Verifying Discord token...")

    async def verify_token():
        """Verify the Discord token by making a simple authenticated request."""
        loop = asyncio.get_event_loop()
        http = HTTPClient(loop=loop)
        try:
            await http.static_login(token)
            user = await http.get_user("@me")
            await http.close()

            bot_name = user.get("username", "Unknown")
            bot_id = user.get("id", "Unknown")

            click.secho("✓ Token authenticated successfully!", fg="green")
            click.echo(f"Bot Name: {bot_name}")
            click.echo(f"Bot ID: {bot_id}")
            click.echo(f"Discriminator: {user.get('discriminator', 'N/A')}")
            return 0
        except LoginFailure:
            click.secho("✗ Token authentication failed. Invalid token.", fg="red")
            return 1
        except HTTPException as e:
            click.secho(f"✗ HTTP error occurred: {e}", fg="red")
            return 1
        except Exception as e:
            click.secho(f"✗ Unexpected error: {e}", fg="red")
            return 1
        finally:
            try:
                await http.close()
            except Exception:
                pass  # Already closed or closing

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(verify_token())

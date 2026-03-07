"""CLI command for starting the chat bot."""

import asyncio
import os

import click

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.command(context_settings={"show_default": True})
@click.option(
    "-t",
    "--token",
    help="Discord bot token (defaults to DISCORD_BOT_TOKEN env var)",
)
@click.option(
    "-p",
    "--prefix",
    default="!",
    help="Command prefix for the Discord bot",
)
@click.option(
    "-c",
    "--channel",
    "channels",
    multiple=True,
    type=int,
    help="Specific channel ID to monitor. Can be specified multiple times. If not specified, all channels are monitored.",
)
@click.option(
    "-i",
    "--ignore-domain",
    "ignore_domains",
    multiple=True,
    help="Domain to ignore when processing URLs. Can be specified multiple times.",
)
@click.option(
    "--raw-path",
    default=config.get("chat.start.raw_articles"),
    type=click.Path(file_okay=True, dir_okay=False, path_type=str),
    help="Path to store raw articles",
)
@click.option(
    "--processed-path",
    default=config.get("chat.start.processed_articles"),
    type=click.Path(file_okay=True, dir_okay=False, path_type=str),
    help="Path to store processed articles",
)
@click.option(
    "-r",
    "--retries",
    default=5,
    type=int,
    help="Maximum number of retries for rate-limited requests",
)
@click.option(
    "--pause",
    default=0.5,
    type=float,
    help="Number of seconds to pause between requests",
)
@click.option(
    "--timeout",
    default=200,
    type=int,
    help="Request timeout in seconds",
)
@click.option(
    "--use-cloudscraper",
    is_flag=True,
    help="Use cloudscraper instead of requests for harder-to-scrape sites",
)
def start(
    token: str | None,
    prefix: str,
    channels: list[int],
    ignore_domains: list[str],
    raw_path: str,
    processed_path: str,
    retries: int,
    pause: float,
    timeout: int,
    use_cloudscraper: bool,
) -> int:
    """Start the Discord agent for URL monitoring and article processing.

    This command starts a Discord bot that monitors channels for URLs,
    retrieves them, processes them using BAML, and stores the results in JSONL files.

    The bot will run until you press Ctrl+C.
    """
    # Import here to avoid circular imports
    from abzu.chat.agent import start_agent

    # Check if DISCORD_BOT_TOKEN is set
    if not token and not os.environ.get("DISCORD_BOT_TOKEN"):
        logger.error("Discord bot token is required. Use --token or set DISCORD_BOT_TOKEN env var.")
        return 1

    # Create agent config
    config = {
        "discord_token": token,
        "command_prefix": prefix,
        "specific_channels": list(channels) if channels else None,
        "ignored_domains": list(ignore_domains) if ignore_domains else None,
        "raw_articles_path": raw_path,
        "processed_articles_path": processed_path,
        "max_retries": retries,
        "pause_seconds": pause,
        "timeout": timeout,
        "use_cloudscraper": use_cloudscraper,
    }

    logger.info("Starting Chat agent...")

    agent = None
    loop = None
    try:
        # Create and start the agent
        loop = asyncio.get_event_loop()
        agent = loop.run_until_complete(start_agent(config))

        # Run until interrupted
        logger.info("Chat agent is running. Press Ctrl+C to stop.")

        # Keep the agent running until interrupted
        # We use a simple loop that waits for keyboard interrupt
        while agent._running:
            try:
                loop.run_until_complete(asyncio.sleep(1.0))
            except KeyboardInterrupt:
                break

    except KeyboardInterrupt:
        logger.info("Stopping Chat agent...")
        try:
            # Stop the agent
            if agent is not None and agent._running and loop is not None:
                loop.run_until_complete(agent.stop())
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")

        logger.info("Chat agent stopped.")
    except Exception as e:
        logger.error(f"Error running Chat agent: {e}")
        return 1

    return 0

"""Discord bot for URL monitoring and processing."""

import asyncio
import logging
import os
import re
from typing import Any, Callable, List, Optional

from discord import Intents, Message, TextChannel, errors
from discord.ext import commands

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class URLMonitorBot(commands.Bot):
    """Discord bot that monitors channels for URLs."""

    def __init__(
        self,
        command_prefix: str = "!",
        intents: Optional[Intents] = None,
        specific_channels: Optional[List[int]] = None,
        ignored_domains: Optional[List[str]] = None,
        on_url_found_callback: Optional[Callable[[str, Message], Any]] = None,
    ):
        """Initialize the Discord bot.

        Args:
            command_prefix: Command prefix for bot commands. Defaults to "!".
            intents: Discord intents. If None, default intents with message content will be used.
            specific_channels: List of specific channel IDs to monitor for URLs.
                               If None, all channels are monitored.
            ignored_domains: List of domains to ignore. Defaults to None.
            on_url_found_callback: Callback function to call when a URL is found.
                Function should accept (url: str, message: Message).
        """
        # Set up intents (permissions)
        if intents is None:
            intents = Intents.default()
            intents.message_content = True  # Need message content to detect URLs
            intents.guilds = True  # Need access to guild information

        super().__init__(command_prefix=command_prefix, intents=intents)

        # URL detection settings
        self.url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        self.specific_channels = set(specific_channels) if specific_channels else None
        self.ignored_domains = set(ignored_domains) if ignored_domains else set()
        self.on_url_found_callback = on_url_found_callback

        # Set up event handlers
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Set up Discord event handlers."""

        @self.event
        async def on_ready():
            """Called when the bot is ready."""
            logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
            logger.info(f"Connected to {len(self.guilds)} guilds")

            # Log all available channels
            channel_count = 0
            for guild in self.guilds:
                logger.info(f"Guild: {guild.name} (ID: {guild.id})")
                text_channels = [ch for ch in guild.channels if isinstance(ch, TextChannel)]
                channel_count += len(text_channels)
                for channel in text_channels:
                    logger.info(f"  - #{channel.name} (ID: {channel.id})")

            # Log monitoring status
            if self.specific_channels:
                logger.info(f"Monitoring specific {len(self.specific_channels)} channels for URLs")
            else:
                logger.info(f"Monitoring all {channel_count} channels for URLs")

            if self.ignored_domains:
                logger.info(f"Ignoring URLs from these domains: {', '.join(self.ignored_domains)}")

            logger.info("Bot is ready!")

        @self.event
        async def on_message(message: Message):
            """Called when a message is received.

            Args:
                message: The Discord message
            """
            # Ignore messages from the bot itself
            if message.author == self.user:
                return

            # Check if it's a text channel
            if not isinstance(message.channel, TextChannel):
                return

            # Check if the channel is in the specific list (if monitoring specific channels)
            if self.specific_channels and message.channel.id not in self.specific_channels:
                return

            # Check for URLs in the message
            urls = self.extract_urls(message.content)

            if urls:
                logger.info(
                    f"Found {len(urls)} URLs in message from {message.author} in #{message.channel.name}"
                )

                # Process each URL (after filtering out ignored domains)
                for url in urls:
                    # Skip ignored domains
                    if any(ignored in url.lower() for ignored in self.ignored_domains):
                        logger.info(f"Ignoring URL from ignored domain: {url}")
                        continue

                    logger.info(f"Processing URL: {url}")

                    # Call the callback if defined
                    if self.on_url_found_callback:
                        try:
                            await self.on_url_found_callback(url, message)
                        except Exception as e:
                            logger.error(f"Error in URL processing callback: {e}")

            # Process commands if any
            await self.process_commands(message)

        @self.event
        async def on_guild_join(guild):
            """Called when the bot joins a new guild.

            Args:
                guild: The Discord guild
            """
            logger.info(f"Bot joined new guild: {guild.name} (ID: {guild.id})")
            # Log all channels in the new guild
            text_channels = [ch for ch in guild.channels if isinstance(ch, TextChannel)]
            logger.info(f"Found {len(text_channels)} text channels in {guild.name}")
            for channel in text_channels:
                logger.info(f"  - #{channel.name} (ID: {channel.id})")

    def extract_urls(self, content: str) -> List[str]:
        """Extract URLs from a string.

        Args:
            content: The string to extract URLs from

        Returns:
            List of URLs found in the string
        """
        if not content:
            return []

        # Find all URLs in the content
        urls = self.url_pattern.findall(content)

        # Filter out duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls


class BotRunner:
    """Helper class to run the Discord bot."""

    def __init__(
        self,
        application_id: Optional[str] = None,
        token: Optional[str] = None,
        command_prefix: str = "!",
        specific_channels: Optional[List[int]] = None,
        ignored_domains: Optional[List[str]] = None,
        on_url_found_callback: Optional[Callable[[str, Message], Any]] = None,
    ):
        """Initialize the bot runner.

        Args:
            application_id: Discord application ID. If None, will be read from DISCORD_APPLICATION_ID environment variable.
            token: Discord bot token. If None, will be read from DISCORD_BOT_TOKEN environment variable.
            command_prefix: Command prefix for bot commands. Defaults to "!".
            specific_channels: List of specific channel IDs to monitor for URLs.
                             If None, all channels are monitored.
            ignored_domains: List of domains to ignore. Defaults to None.
            on_url_found_callback: Callback function to call when a URL is found.
                Function should accept (url: str, message: Message).
        """
        self.application_id = application_id or os.environ.get("DISCORD_APPLICATION_ID")
        if not self.application_id:
            raise ValueError(
                "Discord application ID is required. Set the DISCORD_APPLICATION_ID environment variable."
            )
        if not self.application_id.isdigit():
            raise ValueError(
                "Discord application ID must be a valid integer. Check your DISCORD_APPLICATION_ID environment variable."
            )

        self.token = token or os.environ.get("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError(
                "Discord bot token is required. Set the DISCORD_BOT_TOKEN environment variable."
            )
        if not self.token.isalnum():
            raise ValueError(
                "Discord bot token must be alphanumeric. Check your DISCORD_BOT_TOKEN environment variable."
            )

        self.command_prefix = command_prefix
        self.specific_channels = specific_channels
        self.ignored_domains = ignored_domains
        self.on_url_found_callback = on_url_found_callback
        self.bot = None

    async def start(self):
        """Start the Discord bot."""
        self.bot = URLMonitorBot(
            command_prefix=self.command_prefix,
            specific_channels=self.specific_channels,
            ignored_domains=self.ignored_domains,
            on_url_found_callback=self.on_url_found_callback,
        )

        try:
            logger.info("Starting Discord bot...")
            await self.bot.start(self.token)
        except errors.LoginFailure:
            logger.error(
                "Invalid Discord token. Please check your DISCORD_BOT_TOKEN environment variable."
            )
            raise
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")
            raise

    async def stop(self):
        """Stop the Discord bot."""
        if self.bot:
            logger.info("Stopping Discord bot...")
            await self.bot.close()
            logger.info("Discord bot stopped.")

    def run(self):
        """Run the Discord bot synchronously."""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        except Exception as e:
            logger.error(f"Bot stopped due to error: {e}")
        finally:
            # Ensure cleanup even if an error occurs
            try:
                asyncio.run(self.stop())
            except Exception as e:
                logger.error(f"Error during bot cleanup: {e}")

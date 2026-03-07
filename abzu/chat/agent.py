"""Chat agent for URL monitoring and article processing."""

import asyncio
from typing import Any, cast

from discord import Message
from pydantic import BaseModel, Field

from abzu.baml_client.types import IndustryArticle
from abzu.chat.bot import BotRunner
from abzu.chat.io import ArticleStorage
from abzu.chat.playwright_fetcher import PlaywrightFetcher
from abzu.chat.processor import ArticleProcessor
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


class AgentConfig(BaseModel):
    """Configuration for the DiscordAgent."""

    application_id: str | None = Field(
        None,
        description="Discord application ID. Will use DISCORD_APPLICATION_ID env var if not provided.",
    )
    discord_token: str | None = Field(
        None, description="Discord bot token. Will use DISCORD_BOT_TOKEN env var if not provided."
    )
    command_prefix: str = Field("!", description="Command prefix for the Discord bot.")
    specific_channels: list[int] | None = Field(
        None, description="Specific channel IDs to monitor. If None, all channels are monitored."
    )
    ignored_domains: list[str] | None = Field(
        None, description="Domains to ignore when processing URLs."
    )
    raw_articles_path: str = Field(
        config.get("chat.start.raw_articles"),
        description="Path to store raw articles.",
    )
    processed_articles_path: str = Field(
        config.get("chat.start.processed_articles"),
        description="Path to store processed articles.",
    )
    # Playwright configuration
    browser_type: str = Field(
        config.get("crawl.playwright.browser_type", "chromium"),
        description="Browser type for Playwright: chromium, firefox, or webkit.",
    )
    headless: bool = Field(
        config.get("crawl.playwright.headless", True),
        description="Run browser in headless mode.",
    )
    max_retries: int = Field(
        config.get("crawl.playwright.max_retries", 3),
        description="Maximum number of retries for failed requests.",
    )
    timeout: int = Field(
        config.get("crawl.playwright.timeout", 30),
        description="Page load timeout in seconds.",
    )


class DiscordAgent:
    """Agent for monitoring Discord for URLs and processing articles."""

    config: AgentConfig
    bot_runner: BotRunner | None = None
    playwright_fetcher: PlaywrightFetcher | None = None
    article_processor: ArticleProcessor | None = None
    article_storage: ArticleStorage | None = None
    _bot_task: asyncio.Task[None] | None = None
    _running: bool = False

    def __init__(self, config: AgentConfig | None = None):
        """Initialize the agent.

        Args:
            config: Agent configuration. If None, default config will be used.
        """
        self.config = config or AgentConfig(
            application_id=None,
            discord_token=None,
            command_prefix="!",
            specific_channels=None,
            ignored_domains=None,
            raw_articles_path=config.get("chat.start.raw_articles"),  # type: ignore
            processed_articles_path=config.get("chat.start.processed_articles"),  # type: ignore
            browser_type=config.get("crawl.playwright.browser_type", "chromium"),  # type: ignore
            headless=config.get("crawl.playwright.headless", True),  # type: ignore
            max_retries=config.get("crawl.playwright.max_retries", 3),  # type: ignore
            timeout=config.get("crawl.playwright.timeout", 30),  # type: ignore
        )

        # Initialize components
        self.playwright_fetcher = PlaywrightFetcher(
            max_retries=self.config.max_retries,
            timeout=self.config.timeout,
            headless=self.config.headless,
            browser_type=self.config.browser_type,
        )
        self.article_processor = ArticleProcessor()
        self.article_storage = ArticleStorage(
            raw_articles_path=self.config.raw_articles_path,
            processed_articles_path=self.config.processed_articles_path,
        )

        # Set up bot runner
        self.bot_runner = BotRunner(
            token=self.config.discord_token,
            command_prefix=self.config.command_prefix,
            specific_channels=self.config.specific_channels,
            ignored_domains=self.config.ignored_domains,
            on_url_found_callback=self.process_url,
        )

    async def start(self) -> None:
        """Start the Discord agent."""
        if self._running:
            logger.warning("Agent is already running")
            return

        logger.info("Starting Discord agent...")
        self._running = True

        # Initialize Playwright browser
        if self.playwright_fetcher:
            await self.playwright_fetcher.initialize()
            logger.info("Playwright browser initialized")

        # Start the bot in a background task
        self._bot_task = asyncio.create_task(self._run_bot())

        logger.info("Discord agent started")

    async def stop(self) -> None:
        """Stop the Discord agent."""
        if not self._running:
            logger.warning("Agent is not running")
            return

        logger.info("Stopping Discord agent...")

        # Stop the Discord bot
        if self.bot_runner:
            await self.bot_runner.stop()

        # Close the Playwright browser
        if self.playwright_fetcher:
            await self.playwright_fetcher.close()
            logger.info("Playwright browser closed")

        # Cancel the bot task
        if self._bot_task:
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass
            self._bot_task = None

        self._running = False
        logger.info("Discord agent stopped")

    async def _run_bot(self) -> None:
        """Run the Discord bot in a background task."""
        if not self.bot_runner:
            logger.error("Bot runner not initialized")
            return

        try:
            await self.bot_runner.start()
        except Exception as e:
            logger.error(f"Error running Discord bot: {e}")
            self._running = False

    async def process_url(self, url: str, message: Message) -> None:
        """Process a URL found in a Discord message.

        Args:
            url: The URL to process
            message: The Discord message containing the URL
        """
        if not self.playwright_fetcher or not self.article_processor or not self.article_storage:
            logger.error("Agent components not initialized")
            return

        # Helper function to send error to bots channel
        async def send_error_to_bots(error_msg: str) -> None:
            """Send error message to #bots channel."""
            if not self.bot_runner or not self.bot_runner.bot:
                await message.channel.send(error_msg)
                return

            # Find the #bots channel
            bots_channel = None
            for guild in self.bot_runner.bot.guilds:
                for channel in guild.text_channels:
                    if channel.name == "bots":
                        bots_channel = channel
                        break
                if bots_channel:
                    break

            if bots_channel:
                await bots_channel.send(
                    f"Error processing URL from {message.channel.mention}: {error_msg}"  # type: ignore[union-attr]
                )
            else:
                # Fallback to original channel if #bots not found
                await message.channel.send(error_msg)

        try:
            # Fetch the content using Playwright
            logger.info(f"Fetching content from URL: {url}")
            success, result = await self.playwright_fetcher.fetch_url(url)

            if not success:
                logger.error(f"Failed to fetch URL {url}: {result}")
                await send_error_to_bots(f"Failed to process URL: {url}")
                return

            # Store the raw article
            article = cast(dict[str, Any], result)
            self.article_storage.save_raw_article(article)

            # Process the article
            success, processed_result = await self.article_processor.process_article(article)

            if not success:
                logger.error(f"Failed to process article from URL {url}: {processed_result}")
                await send_error_to_bots(f"Failed to extract information from URL: {url}")
                return

            # Store the processed article
            processed_article = cast(IndustryArticle, processed_result)
            self.article_storage.save_processed_article(processed_article)

            logger.info(f"Successfully processed URL: {url}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await send_error_to_bots(f"Error processing URL: {url}")


async def start_agent(config: dict[str, Any] | None = None) -> DiscordAgent:
    """Create and start a DiscordAgent.

    Args:
        config: Dictionary of configuration options for the agent

    Returns:
        Started DiscordAgent instance
    """
    agent_config = AgentConfig(**(config or {}))
    agent = DiscordAgent(config=agent_config)
    await agent.start()
    return agent

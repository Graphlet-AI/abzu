"""Chat agent for URL monitoring and article processing."""

import asyncio
import logging
from typing import Any, Optional, cast

from discord import Message
from pydantic import BaseModel, Field

from abzu.baml_client.types import IndustryArticle
from abzu.chat.bot import BotRunner
from abzu.chat.fetcher import ContentFetcher
from abzu.chat.io import ArticleStorage
from abzu.chat.processor import ArticleProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for the DiscordAgent."""

    application_id: Optional[str] = Field(
        None,
        description="Discord application ID. Will use DISCORD_APPLICATION_ID env var if not provided.",
    )
    discord_token: Optional[str] = Field(
        None, description="Discord bot token. Will use DISCORD_BOT_TOKEN env var if not provided."
    )
    command_prefix: str = Field("!", description="Command prefix for the Discord bot.")
    specific_channels: Optional[list[int]] = Field(
        None, description="Specific channel IDs to monitor. If None, all channels are monitored."
    )
    ignored_domains: Optional[list[str]] = Field(
        None, description="Domains to ignore when processing URLs."
    )
    raw_articles_path: str = Field(
        "data/chat/raw_articles.jsonl",
        description="Path to store raw articles.",
    )
    processed_articles_path: str = Field(
        "data/chat/processed_articles.jsonl",
        description="Path to store processed articles.",
    )
    max_retries: int = Field(5, description="Maximum number of retries for rate-limited requests.")
    pause_seconds: float = Field(0.5, description="Number of seconds to pause between requests.")
    timeout: int = Field(30, description="Request timeout in seconds.")
    use_cloudscraper: bool = Field(
        False, description="Whether to use cloudscraper instead of requests."
    )


class DiscordAgent:
    """Agent for monitoring Discord for URLs and processing articles."""

    config: AgentConfig
    bot_runner: Optional[BotRunner] = None
    content_fetcher: Optional[ContentFetcher] = None
    article_processor: Optional[ArticleProcessor] = None
    article_storage: Optional[ArticleStorage] = None
    _bot_task: Optional[asyncio.Task] = None
    _running: bool = False

    def __init__(self, config: Optional[AgentConfig] = None):
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
            raw_articles_path="data/chat/raw_articles.jsonl",
            processed_articles_path="data/chat/processed_articles.jsonl",
            max_retries=5,
            pause_seconds=0.5,
            timeout=30,
            use_cloudscraper=False,
        )

        # Initialize components
        self.content_fetcher = ContentFetcher(
            max_retries=self.config.max_retries,
            pause_seconds=self.config.pause_seconds,
            timeout=self.config.timeout,
            use_cloudscraper=self.config.use_cloudscraper,
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

    async def start(self):
        """Start the Discord agent."""
        if self._running:
            logger.warning("Agent is already running")
            return

        logger.info("Starting Discord agent...")
        self._running = True

        # Start the bot in a background task
        self._bot_task = asyncio.create_task(self._run_bot())

        logger.info("Discord agent started")

    async def stop(self):
        """Stop the Discord agent."""
        if not self._running:
            logger.warning("Agent is not running")
            return

        logger.info("Stopping Discord agent...")

        # Stop the Discord bot
        if self.bot_runner:
            await self.bot_runner.stop()

        # Close the content fetcher
        if self.content_fetcher:
            self.content_fetcher.close()

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

    async def _run_bot(self):
        """Run the Discord bot in a background task."""
        if not self.bot_runner:
            logger.error("Bot runner not initialized")
            return

        try:
            await self.bot_runner.start()
        except Exception as e:
            logger.error(f"Error running Discord bot: {e}")
            self._running = False

    async def process_url(self, url: str, message: Message):
        """Process a URL found in a Discord message.

        Args:
            url: The URL to process
            message: The Discord message containing the URL
        """
        if not self.content_fetcher or not self.article_processor or not self.article_storage:
            logger.error("Agent components not initialized")
            return

        try:
            # Fetch the content
            logger.info(f"Fetching content from URL: {url}")
            success, result = self.content_fetcher.fetch_url(url)

            if not success:
                logger.error(f"Failed to fetch URL {url}: {result}")
                await message.channel.send(f"Failed to process URL: {url}")
                return

            # Store the raw article
            article = cast(dict[str, Any], result)
            self.article_storage.save_raw_article(article)

            # Process the article
            success, processed_result = self.article_processor.process_article(article)

            if not success:
                logger.error(f"Failed to process article from URL {url}: {processed_result}")
                await message.channel.send(f"Failed to extract information from URL: {url}")
                return

            # Store the processed article
            processed_article = cast(IndustryArticle, processed_result)
            self.article_storage.save_processed_article(processed_article)

            logger.info(f"Successfully processed URL: {url}")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            await message.channel.send(f"Error processing URL: {url}")


async def start_agent(config: Optional[dict[str, Any]] = None) -> DiscordAgent:
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

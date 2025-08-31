"""CLI module for crawling content from various sources."""

import click

from abzu.cli.crawl.datacenter import datacenter
from abzu.cli.crawl.dcbyte import dcbyte
from abzu.cli.crawl.reddit import reddit
from abzu.cli.crawl.rss import rss
from abzu.cli.crawl.semianalysis import semianalysis
from abzu.cli.crawl.theinformation import theinformation
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--all",
    is_flag=True,
    help="Crawl all sources: datacenter, semianalysis, theinformation, and rss",
)
@click.pass_context
def crawl(ctx, all):
    """Crawl content from various sources."""
    if all:
        logger.info("Starting crawl of all sources: datacenter, semianalysis, theinformation, rss")

        # Track results
        results = {}

        # Crawl each source using Click command invocation
        sources = [
            ("datacenter", datacenter),
            ("semianalysis", semianalysis),
            ("theinformation", theinformation),
            ("rss", rss),
        ]

        for source_name, command in sources:
            logger.info(f"Crawling {source_name}...")
            try:
                result = ctx.invoke(command)
                results[source_name] = result
                logger.info(f"{source_name.title()} crawl completed: {result}")
            except Exception as e:
                logger.error(f"{source_name.title()} crawl failed: {e}")
                results[source_name] = f"Failed: {e}"

        # Summary
        logger.info("=" * 60)
        logger.info("CRAWL ALL SUMMARY:")
        for source, result in results.items():
            logger.info(f"  {source}: {result}")
        logger.info("=" * 60)

        return results
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


crawl.add_command(datacenter)
crawl.add_command(dcbyte)
crawl.add_command(semianalysis)
crawl.add_command(theinformation)
crawl.add_command(rss)
crawl.add_command(reddit)

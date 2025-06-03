"""CLI module for crawling content from various sources."""

import click

from abzu.cli.crawl.reddit import reddit
from abzu.cli.crawl.rss import rss
from abzu.cli.crawl.semianalysis import semianalysis
from abzu.cli.crawl.theinformation import theinformation


@click.group()
def crawl():
    """Crawl content from various sources."""
    pass


crawl.add_command(semianalysis)
crawl.add_command(theinformation)
crawl.add_command(rss)
crawl.add_command(reddit)

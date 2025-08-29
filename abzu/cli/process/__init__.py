"""CLI module for processing commands."""

import click

from abzu.cli.process.articles import articles
from abzu.cli.process.er import er
from abzu.cli.process.kg import kg
from abzu.cli.process.rss import rss
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--all",
    is_flag=True,
    help="Run the full processing pipeline: articles -> rss -> kg raw -> er block -> er match",
)
@click.pass_context
def process(ctx, all):
    """Process data for knowledge extraction."""
    if all:
        logger.info(
            "Starting full processing pipeline: articles -> rss -> kg raw -> er block -> er match"
        )

        # Track results
        results = {}

        # Processing pipeline steps
        steps = [
            ("articles semianalysis", articles.commands["semianalysis"]),
            ("articles theinformation", articles.commands["theinformation"]),
            ("articles datacenter", articles.commands["datacenter"]),
            ("articles dcbyte", articles.commands["dcbyte"]),
            ("articles reddit", articles.commands["reddit"]),
            ("rss processing", rss),
            ("kg raw", kg.commands["raw"]),
            ("er block", er.commands["block"]),
            ("er match", er.commands["match"]),
        ]

        for step_name, command in steps:
            logger.info(f"Running {step_name}...")
            try:
                result = ctx.invoke(command)
                results[step_name] = result or "Completed"
                logger.info(f"{step_name} completed: {result or 'Success'}")
            except Exception as e:
                logger.error(f"{step_name} failed: {e}")
                results[step_name] = f"Failed: {e}"
                # Continue with next step even if one fails

        # Summary
        logger.info("=" * 60)
        logger.info("PROCESSING PIPELINE SUMMARY:")
        for step, result in results.items():
            logger.info(f"  {step}: {result}")
        logger.info("=" * 60)

        return results
    elif ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


process.add_command(articles)
process.add_command(er)
process.add_command(kg)
process.add_command(rss)

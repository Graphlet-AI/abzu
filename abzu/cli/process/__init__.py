"""CLI module for processing commands."""

from typing import Any

import click


# Lazy loading group that only imports subcommands when needed
class LazyGroup(click.Group):
    """A Click group that loads subcommands lazily."""

    def __init__(
        self, *args: Any, lazy_subcommands: dict[str, str] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str] = lazy_subcommands or {}

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(self.lazy_subcommands.keys())

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self.lazy_subcommands:
            # Import the subcommand module only when accessed
            import_path = self.lazy_subcommands[name]
            module_name, attr_name = import_path.rsplit(":", 1)
            module = __import__(module_name, fromlist=[attr_name])
            return getattr(module, attr_name)
        return None


@click.command(
    cls=LazyGroup,
    lazy_subcommands={
        "articles": "abzu.cli.process.articles:articles",
        "er": "abzu.cli.process.er:er",
        "kg": "abzu.cli.process.kg:kg",
        "rss": "abzu.cli.process.rss:rss",
    },
    invoke_without_command=True,
)
@click.option(
    "--all",
    is_flag=True,
    help="Run the full processing pipeline: articles -> rss -> kg raw -> er block -> er match",
)
@click.pass_context
def process(ctx: click.Context, all: bool) -> dict[str, int | str] | None:
    """Process data for knowledge extraction."""
    if all:
        # Import logger only when needed
        from abzu.logs import get_logger

        logger = get_logger(__name__)

        # Import subcommands only when --all is used
        from abzu.cli.process.articles import articles
        from abzu.cli.process.er import er
        from abzu.cli.process.kg import kg
        from abzu.cli.process.rss import rss

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

    return None

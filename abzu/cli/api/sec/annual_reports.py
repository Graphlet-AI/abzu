"""Commands for working with SEC annual reports."""

import click

from abzu.api.annual_report_kuzu import build_annual_report_kuzu_graph
from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


@click.group(name="annual-reports")
def annual_reports() -> None:
    """Operations on processed annual reports."""


@annual_reports.group()
def build() -> None:
    """Build resources from annual report data."""


@build.command("kuzu", context_settings={"show_default": True})
@click.option(
    "-i",
    "--input-dir",
    default=config.get("api.sec.download.annual_reports"),
    help="Directory with processed annual reports",
)
@click.option(
    "-o",
    "--output-dir",
    default=config.get("api.sec.build_kuzu.output_dir"),
    help="Directory to write Kuzu CSV files",
)
def build_kuzu(input_dir: str, output_dir: str) -> None:
    """Build a Kuzu graph from processed annual reports."""
    paths = build_annual_report_kuzu_graph(input_dir, output_dir)
    logger.info("Saved companies CSV to %s", paths["companies"])
    for key in (
        "invests_in",
        "has_investor",
        "partnered_with",
        "supplies",
        "has_supplier",
    ):
        logger.info("Saved %s CSV to %s", key, paths[key])
    click.secho(f"Saved companies CSV to {paths['companies']}", fg="green")
    for key in (
        "invests_in",
        "has_investor",
        "partnered_with",
        "supplies",
        "has_supplier",
    ):
        click.secho(f"Saved {key} CSV to {paths[key]}", fg="green")

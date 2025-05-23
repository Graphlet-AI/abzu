"""CLI command for processing SemiAnalysis articles."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    default=config.get("process.articles.semianalysis.input"),
    help=f"Input JSONL file path (default: {config.get('process.articles.semianalysis.input')})",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default=config.get("process.articles.semianalysis.output"),
    help=f"Output JSONL file path (default: {config.get('process.articles.semianalysis.output')})",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=5,
    help="Number of articles to process concurrently (default: 5)",
)
def process_semianalysis(input_file, output_file, batch_size):
    """Process SemiAnalysis articles through LLM extraction pipeline."""
    from abzu.articles.processor import process_main

    return process_main(
        input_file=input_file,
        output_file=output_file,
        batch_size=batch_size,
    )

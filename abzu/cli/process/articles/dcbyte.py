"""CLI command for processing dcbyte articles."""

import click

from abzu.config import config


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    default=config.get("process.articles.dcbyte.input"),
    type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=str),
    help="Input JSONL file path",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default=config.get("process.articles.dcbyte.output"),
    type=click.Path(dir_okay=False, file_okay=True, path_type=str),
    help="Output JSONL file path",
)
@click.option(
    "-b",
    "--batch-size",
    type=int,
    default=5,
    help="Number of articles to process concurrently (default: 5)",
)
def process_dcbyte(input_file, output_file, batch_size):
    """Process dcbyte articles through LLM extraction pipeline."""
    from abzu.articles.processor import process_main

    return process_main(
        input_file=input_file,
        output_file=output_file,
        batch_size=batch_size,
    )

"""CLI command for processing SemiAnalysis articles."""

import click


@click.command(context_settings={"show_default": True})
@click.option(
    "-i",
    "--input",
    "input_file",
    default="data/semianalysis.jsonl",
    help="Input JSONL file path (default: data/semianalysis.jsonl)",
)
@click.option(
    "-o",
    "--output",
    "output_file",
    default="data/processed_semianalysis.jsonl",
    help="Output JSONL file path (default: data/processed_semianalysis.jsonl)",
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

"""
Module for handling the pipeline steps functionality.
"""

from typing import List


def get_pipeline_steps() -> List[str]:
    """
    Get the ordered list of steps required to run the complete data pipeline.

    Returns
    -------
    List[str]
        List of command strings representing the pipeline steps.
    """
    return [
        "baml-cli generate",
        "abzu crawl semianalysis",
        "abzu process articles semianalysis",
        "abzu process kg raw",
        "abzu api financialdatasets --file data/knowledge_graph/tickers.parquet",
        "abzu process kg refine",
        "abzu api sec download",
    ]


def print_pipeline_steps() -> None:
    """
    Print the ordered list of steps required to run the complete data pipeline.
    """
    steps = get_pipeline_steps()

    print("Complete Pipeline Steps:")
    for idx, step in enumerate(steps, 1):
        print(f"{idx}. Run '{step}'")

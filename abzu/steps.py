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
        # Get financial data for companies extracted from knowledge graph
        "abzu api financialdatasets facts --file data/knowledge_graph/tickers.parquet",
        # Get financial metrics for key companies
        "abzu api financialdatasets metrics -t NVDA -t AMD -t INTC -P annual -l 5",
        # Get historical price data for key companies
        "abzu api financialdatasets price-multiple -t NVDA -t AMD -t INTC -s 2023-01-01 -e 2023-12-31 -i day -o data/financialdatasets/chip_prices.json",
        "abzu process kg refine",
    ]


def print_pipeline_steps() -> None:
    """
    Print the ordered list of steps required to run the complete data pipeline.
    """
    steps = get_pipeline_steps()

    print("Complete Pipeline Steps:")
    for idx, step in enumerate(steps, 1):
        print(f"{idx}. Run '{step}'")

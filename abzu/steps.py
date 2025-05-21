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
        # Run Discord bot to monitor channels for articles
        "abzu chat start",
        # Crawl semianalysis.com for articles
        "abzu crawl semianalysis",
        # Crawl theinformation.com for articles
        "abzu crawl theinformation",
        # Process the collected articles
        "abzu process articles semianalysis",
        "abzu process articles theinformation",
        # Build a separate node / edge list parquet file for each type of node / edge
        "abzu process kg raw",
        # Get financial data for companies extracted from knowledge graph
        "abzu api financialdatasets facts --file data/knowledge_graph/tickers.parquet",
        # Get financial metrics for key companies
        "abzu api financialdatasets metrics -t NVDA -t AMD -t INTC -P annual -l 5",
        # Get historical price data for all tickers extracted from the knowledge graph
        "abzu api financialdatasets price -f data/knowledge_graph/tickers.parquet -s 2025-01-01 -e 2025-12-31 -i day -o data/financialdatasets/all_prices.json",
        # Summarize best performing stocks
        "abzu dump returns -f data/financialdatasets/all_prices.json",
        # Download SEC filings for companies
        "abzu api sec download",
        # Build a single node / edge list in GraphFrames format
        "abzu process kg refine",
        # List all products found in the refined knowledge graph
        "abzu dump products -f data/refined_knowledge_graph/products.parquet",
    ]


def print_pipeline_steps() -> None:
    """
    Print the ordered list of steps required to run the complete data pipeline.
    """
    steps = get_pipeline_steps()

    print("Complete Pipeline Steps:")
    for idx, step in enumerate(steps, 1):
        print(f"{idx}. Run '{step}'")

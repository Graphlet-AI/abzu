"""
Module for handling the pipeline steps functionality.
"""


def get_pipeline_steps() -> list[str]:
    """
    Get the ordered list of steps required to run the complete data pipeline.

    Returns
    -------
    list[str]
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
        # Crawl generic RSS feeds defined in feeds.txt
        "abzu crawl rss -f feeds.txt",
        # Process the collected RSS articles
        "abzu process rss -f feeds.txt",
        # Process the collected articles
        "abzu process articles semianalysis",
        "abzu process articles theinformation",
        # Build a separate node / edge list parquet file for each type of node / edge
        "abzu process kg raw",
        # Get financial data for companies extracted from knowledge graph
        "abzu api financialdatasets facts --file",
        # Get financial metrics for key companies
        "abzu api financialdatasets metrics --file -P annual -l 5",
        # Get historical price data for all tickers extracted from the knowledge graph
        "abzu api financialdatasets price --file -s 2025-01-01 -e <today> -i day",
        # Summarize best performing stocks
        "abzu dump returns -f data/financialdatasets/price.json",
        # Download SEC filings for companies
        "abzu api sec download",
        # Download annual reports for key companies (optional - specify ticker and year)
        "abzu api sec annual-report --ticker <TICKER> --year <YEAR>",
        # Build a single node / edge list in GraphFrames format
        "abzu process kg refine",
        # List all products found in the refined knowledge graph
        "abzu dump products -f data/refined_knowledge_graph/products.parquet",
        # List all companies found in the refined knowledge graph
        "abzu dump companies -f data/refined_knowledge_graph/companies.parquet",
    ]


def print_pipeline_steps() -> None:
    """
    Print the ordered list of steps required to run the complete data pipeline.
    """
    steps = get_pipeline_steps()

    print("Complete Pipeline Steps:")
    for idx, step in enumerate(steps, 1):
        print(f"{idx}. Run '{step}'")

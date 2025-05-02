"""CLI tools for Abzu."""

import argparse
import logging
import sys
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main(args: Optional[List[str]] = None) -> int:  # noqa: C901
    """Main entry point for the abzu command line interface."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Abzu - Industry knowledge extraction")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Process command
    process_cmd = subparsers.add_parser("process", help="Processing commands")
    process_subparsers = process_cmd.add_subparsers(dest="subcommand", help="Process subcommands")

    # Articles subcommand
    articles_cmd = process_subparsers.add_parser("articles", help="Process articles")
    articles_cmd.add_argument(
        "-i",
        "--input",
        default="data/semianalysis.jsonl",
        help="Input JSONL file path (default: data/semianalysis.jsonl)",
    )
    articles_cmd.add_argument(
        "-o",
        "--output",
        default="data/processed_semianalysis.jsonl",
        help="Output JSONL file path (default: data/processed_semianalysis.jsonl)",
    )
    articles_cmd.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=5,
        help="Number of articles to process concurrently (default: 5)",
    )

    # Knowledge Graph subcommand
    kg_cmd = process_subparsers.add_parser("kg", help="Process articles into a knowledge graph")
    kg_subparsers = kg_cmd.add_subparsers(
        dest="kg_subcommand", help="Knowledge graph processing subcommands"
    )

    # KG Raw subcommand - Extracts raw knowledge graph
    kg_raw_cmd = kg_subparsers.add_parser(
        "raw", help="Extract raw knowledge graph from processed articles"
    )
    kg_raw_cmd.add_argument(
        "-i",
        "--input",
        default="data/processed_semianalysis.jsonl",
        help="Input processed articles JSONL file (default: data/processed_semianalysis.jsonl)",
    )
    kg_raw_cmd.add_argument(
        "-o",
        "--output",
        default="data/knowledge_graph",
        help="Output directory for knowledge graph (default: data/knowledge_graph)",
    )
    kg_raw_cmd.add_argument(
        "-p",
        "--partitions",
        type=int,
        default=4,
        help="Number of Spark partitions (default: 4)",
    )

    # KG Refine subcommand - Creates bidirectional edges
    kg_refine_cmd = kg_subparsers.add_parser(
        "refine", help="Refine knowledge graph by creating bidirectional relationships"
    )
    kg_refine_cmd.add_argument(
        "-i",
        "--input",
        default="data/knowledge_graph",
        help="Input directory with raw knowledge graph (default: data/knowledge_graph)",
    )
    kg_refine_cmd.add_argument(
        "-o",
        "--output",
        default="data/refined_knowledge_graph",
        help="Output directory for refined knowledge graph (default: data/refined_knowledge_graph)",
    )
    kg_refine_cmd.add_argument(
        "-p",
        "--partitions",
        type=int,
        default=4,
        help="Number of Spark partitions (default: 4)",
    )

    # Add required KG subcommand help
    kg_cmd.set_defaults(kg_subcommand=argparse.SUPPRESS)

    # Crawl command
    crawl_cmd = subparsers.add_parser("crawl", help="Crawl content from sources")
    crawl_subparsers = crawl_cmd.add_subparsers(dest="crawl_subcommand", help="Crawl subcommands")

    # SemiAnalysis subcommand
    semianalysis_cmd = crawl_subparsers.add_parser(
        "semianalysis", help="Crawl SemiAnalysis website"
    )
    semianalysis_cmd.add_argument(
        "-u", "--url", help="URL to start crawling from (defaults to predefined archive URLs)"
    )
    semianalysis_cmd.add_argument(
        "-o",
        "--output",
        default="data/semianalysis.jsonl",
        help="Output JSONL file path (default: data/semianalysis.jsonl)",
    )
    semianalysis_cmd.add_argument(
        "--pages", type=int, default=24, help="Number of pages to crawl (default: 24)"
    )
    semianalysis_cmd.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=5,
        help="Number of pages to crawl concurrently (default: 5)",
    )
    semianalysis_cmd.add_argument(
        "-c",
        "--concurrent-requests",
        type=int,
        default=5,
        help="Number of concurrent requests per spider (default: 5)",
    )

    # Add required crawl subcommand help
    crawl_cmd.set_defaults(crawl_subcommand=argparse.SUPPRESS)

    # API command
    api_cmd = subparsers.add_parser("api", help="API access to external data sources")
    api_subparsers = api_cmd.add_subparsers(dest="api_subcommand", help="API subcommands")

    # Financial Datasets subcommand
    financialdatasets_cmd = api_subparsers.add_parser(
        "financialdatasets", help="Financial Datasets API access"
    )
    financialdatasets_subparsers = financialdatasets_cmd.add_subparsers(
        dest="financialdatasets_subcommand", help="Financial Datasets API subcommands"
    )

    # Facts subcommand
    facts_cmd = financialdatasets_subparsers.add_parser(
        "facts", help="Get company facts from Financial Datasets API"
    )
    facts_cmd.add_argument("-t", "--ticker", help="Company ticker symbol (e.g., AAPL)")
    facts_cmd.add_argument("-c", "--cik", help="Company Central Index Key (e.g., 0000320193)")
    facts_cmd.add_argument(
        "-f", "--file", help="Path to JSONL file with records containing 'ticker' or 'cik' field"
    )
    facts_cmd.add_argument(
        "-k",
        "--api-key",
        help="API key for Financial Datasets (defaults to FINANCIAL_DATASETS_API_KEY env var)",
    )
    facts_cmd.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        help="Format JSON output with indentation (only when printing to stdout)",
    )
    facts_cmd.add_argument(
        "-o", "--output", help="Output file path (if not provided, prints to stdout)"
    )

    # Add required subcommand help
    financialdatasets_cmd.set_defaults(financialdatasets_subcommand=argparse.SUPPRESS)
    api_cmd.set_defaults(api_subcommand=argparse.SUPPRESS)

    # Parse args
    parsed_args = parser.parse_args(args)

    # Execute command
    if parsed_args.command == "process":
        if parsed_args.subcommand == "articles":
            from abzu.cli.process_articles import process_main

            return process_main(
                input_file=parsed_args.input,
                output_file=parsed_args.output,
                batch_size=parsed_args.batch_size,
            )
        elif parsed_args.subcommand == "kg":
            # Import here to avoid loading Spark when not needed
            from abzu.cli.process_kg import process_raw_kg, process_refine_kg

            if not hasattr(parsed_args, "kg_subcommand") or not parsed_args.kg_subcommand:
                kg_cmd.print_help()
                logger.error("\nError: Please specify a knowledge graph subcommand (raw or refine)")
                return 1

            if parsed_args.kg_subcommand == "raw":
                return process_raw_kg(
                    input_file=parsed_args.input,
                    output_dir=parsed_args.output,
                    partitions=parsed_args.partitions,
                )
            elif parsed_args.kg_subcommand == "refine":
                return process_refine_kg(
                    input_dir=parsed_args.input,
                    output_dir=parsed_args.output,
                    partitions=parsed_args.partitions,
                )
            else:
                kg_cmd.print_help()
                return 1
        else:
            process_cmd.print_help()
            return 1
    elif parsed_args.command == "crawl":
        if not hasattr(parsed_args, "crawl_subcommand") or not parsed_args.crawl_subcommand:
            crawl_cmd.print_help()
            logger.error("\nError: Please specify a crawl subcommand (semianalysis)")
            return 1

        if parsed_args.crawl_subcommand == "semianalysis":
            from abzu.cli.crawl import crawl_main

            return crawl_main(
                url=parsed_args.url,
                output_path=parsed_args.output,
                pages=parsed_args.pages,
                batch_size=parsed_args.batch_size,
                concurrent_requests=parsed_args.concurrent_requests,
            )
        else:
            crawl_cmd.print_help()
            return 1
    elif parsed_args.command == "api":
        if not hasattr(parsed_args, "api_subcommand") or not parsed_args.api_subcommand:
            api_cmd.print_help()
            logger.error("\nError: Please specify an API subcommand (financialdatasets)")
            return 1

        if parsed_args.api_subcommand == "financialdatasets":
            if (
                not hasattr(parsed_args, "financialdatasets_subcommand")
                or not parsed_args.financialdatasets_subcommand
            ):
                financialdatasets_cmd.print_help()
                logger.error("\nError: Please specify a Financial Datasets API subcommand (facts)")
                return 1

            if parsed_args.financialdatasets_subcommand == "facts":
                from abzu.cli.api import financialdatasets_facts_main

                return financialdatasets_facts_main(
                    ticker=parsed_args.ticker,
                    cik=parsed_args.cik,
                    input_file=parsed_args.file,
                    api_key=parsed_args.api_key,
                    pretty=parsed_args.pretty,
                    output_file=parsed_args.output,
                )
            else:
                financialdatasets_cmd.print_help()
                return 1
        else:
            api_cmd.print_help()
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

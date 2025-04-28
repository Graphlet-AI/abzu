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


def main(args: Optional[List[str]] = None) -> int:
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
        default="data/articles.jsonl",
        help="Input JSONL file path (default: data/articles.jsonl)",
    )
    articles_cmd.add_argument(
        "-o",
        "--output",
        default="data/processed_articles.jsonl",
        help="Output JSONL file path (default: data/processed_articles.jsonl)",
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
        default="data/processed_articles.jsonl",
        help="Input processed articles JSONL file (default: data/processed_articles.jsonl)",
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
    crawl_cmd.add_argument(
        "-u", "--url", help="URL to start crawling from (defaults to predefined archive URLs)"
    )
    crawl_cmd.add_argument(
        "-o",
        "--output",
        default="data/articles.jsonl",
        help="Output JSONL file path (default: data/articles.jsonl)",
    )
    crawl_cmd.add_argument(
        "--pages", type=int, default=24, help="Number of pages to crawl (default: 24)"
    )
    crawl_cmd.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=5,
        help="Number of pages to crawl concurrently (default: 5)",
    )
    crawl_cmd.add_argument(
        "-c",
        "--concurrent-requests",
        type=int,
        default=5,
        help="Number of concurrent requests per spider (default: 5)",
    )

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
        from abzu.cli.crawl import crawl_main

        return crawl_main(
            url=parsed_args.url,
            output_path=parsed_args.output,
            pages=parsed_args.pages,
            batch_size=parsed_args.batch_size,
            concurrent_requests=parsed_args.concurrent_requests,
        )
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

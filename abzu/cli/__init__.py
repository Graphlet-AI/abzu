"""CLI tools for Abzu."""

import argparse
import sys
from typing import List, Optional


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

    # Parse args
    parsed_args = parser.parse_args(args)

    # Execute command
    if parsed_args.command == "process":
        if parsed_args.subcommand == "articles":
            from abzu.cli.process_articles import process_main

            return process_main(parsed_args.input, parsed_args.output)
        else:
            process_cmd.print_help()
            return 1
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

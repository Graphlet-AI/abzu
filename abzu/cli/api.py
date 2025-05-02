"""API access module for Abzu CLI."""

import logging

from abzu.api.financialdatasets import financialdatasets_facts_main

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Command line interface for API module."""
    return financialdatasets_facts_main()


if __name__ == "__main__":
    import sys

    sys.exit(main())

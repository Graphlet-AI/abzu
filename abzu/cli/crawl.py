"""CLI wrapper for crawl functionality."""

import logging
import sys
from typing import Optional

from abzu.crawl import DEFAULT_PATH, crawl_semianalysis

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def crawl_main(
    url: Optional[str] = None,
    output_path: str = DEFAULT_PATH,
    pages: int = 24,
    batch_size: int = 1,
    concurrent_requests: int = 1,
) -> int:
    """CLI wrapper for crawling articles from specified URLs in batch mode."""
    return crawl_semianalysis(
        url=url,
        output_path=output_path,
        pages=pages,
        batch_size=batch_size,
        concurrent_requests=concurrent_requests,
    )


def main() -> int:
    """Command line interface for crawler."""
    return crawl_main()


if __name__ == "__main__":
    sys.exit(main())

"""DC Byte blog crawler module."""

from abzu.crawl.dcbyte.extract_html import main as extract_mhtml


def crawl_dcbyte(output_path: str | None = None, pages: int = 10, batch_size: int = 1) -> int:
    """Crawl DC Byte blog articles.

    Args:
        output_path: Path to save crawled articles (defaults to config)
        pages: Number of pages to load (for compatibility - not used in MHTML extraction)
        batch_size: Number of pages to crawl concurrently (for API consistency)

    Returns:
        Number of articles processed
    """
    # For now, we only support MHTML extraction
    # The pages parameter is kept for CLI compatibility but not used
    extract_mhtml()

    # Count articles in the output file
    from pathlib import Path

    output_file = Path(output_path or "data/articles/dcbyte.jsonl")
    if output_file.exists():
        with open(output_file) as f:
            return sum(1 for line in f if line.strip())
    return 0

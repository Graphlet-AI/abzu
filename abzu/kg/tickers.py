"""Ticker matching module for enriching companies with SEC ticker data.

Uses embedding-based similarity to match company names from SEC tickers
to company names in the knowledge graph.
"""

import json
from pathlib import Path
from typing import Any, Literal

import numpy as np
import requests
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from tqdm import tqdm

from abzu.config import config
from abzu.logs import get_logger
from abzu.utils import load_jsonl, save_jsonl

logger = get_logger(__name__)

USER_AGENT = "AbzuBot/1.0 (russell.jurney@gmail.com)"


def download_sec_tickers(
    cache_path: str = config.get("process.kg.tickers.cache"),
    url: str = config.get("process.kg.tickers.url"),
    force: bool = False,
) -> str:
    """Download SEC tickers from SEC EDGAR if not cached.

    Args:
        cache_path: Path to cache the downloaded file
        url: URL to download SEC tickers from
        force: Force re-download even if cached

    Returns:
        Path to the downloaded/cached file
    """
    cache_file = Path(cache_path)

    if cache_file.exists() and not force:
        logger.info(f"Using cached SEC tickers from {cache_path}")
        return cache_path

    logger.info(f"Downloading SEC tickers from {url}")

    cache_file.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()

    with open(cache_path, "w") as f:
        f.write(response.text)

    logger.info(f"Downloaded and cached SEC tickers to {cache_path}")
    return cache_path


def load_tickers(tickers_path: str) -> list[dict[str, Any]]:
    """Load tickers from JSON or JSONL file.

    Supports:
    - SEC company_tickers_exchange.json format: {"fields": [...], "data": [[cik, name, ticker, exchange], ...]}
    - SEC company_tickers.json format: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
    - JSONL format: {"name": ..., "symbol": ..., "exchange": ...}

    Args:
        tickers_path: Path to the tickers file

    Returns:
        List of ticker dictionaries normalized to {cik, symbol, name, exchange} format
    """
    logger.info(f"Loading tickers from {tickers_path}")

    if tickers_path.endswith(".json"):
        with open(tickers_path) as f:
            data = json.load(f)

        # SEC exchange format: {"fields": ["cik", "name", "ticker", "exchange"], "data": [[...], ...]}
        if "fields" in data and "data" in data:
            fields = data["fields"]
            tickers = []
            for row in data["data"]:
                record = dict(zip(fields, row))
                tickers.append(
                    {
                        "cik": record.get("cik"),
                        "symbol": record.get("ticker", ""),
                        "name": record.get("name", ""),
                        "exchange": record.get("exchange"),
                    }
                )
        # Old SEC format: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
        elif isinstance(data, dict) and all(k.isdigit() for k in list(data.keys())[:10]):
            tickers = [
                {
                    "cik": int(v.get("cik_str", 0)) if v.get("cik_str") else None,
                    "symbol": v.get("ticker", ""),
                    "name": v.get("title", ""),
                    "exchange": None,
                }
                for v in data.values()
            ]
        else:
            raise ValueError(f"Unknown JSON format in {tickers_path}")
    else:
        # JSONL format - normalize field names if needed
        raw_tickers = load_jsonl(tickers_path)
        tickers = [
            {
                "cik": t.get("cik"),
                "symbol": t.get("symbol", t.get("ticker", "")),
                "name": t.get("name", t.get("title", "")),
                "exchange": t.get("exchange"),
            }
            for t in raw_tickers
        ]

    logger.info(f"Loaded {len(tickers):,} tickers")
    return tickers


def load_companies(companies_path: str) -> list[dict[str, Any]]:
    """Load companies from Parquet file or directory.

    Args:
        companies_path: Path to the companies.parquet file or Spark output directory

    Returns:
        List of company dictionaries
    """
    import math

    import numpy as np
    import pandas as pd

    logger.info(f"Loading companies from {companies_path}")

    # Pandas read_parquet handles both files and directories
    df = pd.read_parquet(companies_path)

    # Convert to list of dicts
    companies = df.to_dict(orient="records")

    # Replace NaN/NaT with None for Pydantic compatibility
    # Pandas converts null integers to float NaN, which Pydantic rejects
    for company in companies:
        for key, value in company.items():
            if isinstance(value, float) and math.isnan(value):
                company[key] = None
            elif isinstance(value, np.floating) and np.isnan(value):
                company[key] = None
            elif pd.isna(value):
                company[key] = None

    logger.info(f"Loaded {len(companies):,} companies")
    return companies


class TickerMatcher:
    """Match companies with SEC tickers using embedding similarity."""

    def __init__(self, model_name: str = "intfloat/e5-base-v2"):
        """Initialize the ticker matcher with an embedding model.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        device: Literal["cpu", "cuda", "mps"]
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        logger.info(f"Loading embedding model {model_name} on {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.device = device

    def encode_names(self, names: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode company names into embeddings.

        Args:
            names: List of company names
            batch_size: Batch size for encoding

        Returns:
            Numpy array of embeddings
        """
        embeddings = self.model.encode(
            names,
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=batch_size,
        )
        return embeddings

    def find_matches(
        self,
        company_names: list[str],
        ticker_names: list[str],
        threshold: float = 0.85,
    ) -> list[tuple[int, int, float]]:
        """Find matches between company names and ticker names.

        Args:
            company_names: List of company names from KG
            ticker_names: List of company names from SEC tickers
            threshold: Minimum similarity threshold for a match

        Returns:
            List of (company_idx, ticker_idx, similarity) tuples
        """
        logger.info(f"Encoding {len(company_names):,} company names...")
        company_embeddings = self.encode_names(company_names)

        logger.info(f"Encoding {len(ticker_names):,} ticker names...")
        ticker_embeddings = self.encode_names(ticker_names)

        logger.info("Computing similarities...")
        # Compute cosine similarity matrix
        similarities = cos_sim(company_embeddings, ticker_embeddings).numpy()

        # Find best matches above threshold
        matches = []
        for i in tqdm(range(len(company_names)), desc="Finding matches"):
            best_j = int(np.argmax(similarities[i]))
            best_sim = float(similarities[i, best_j])
            if best_sim >= threshold:
                matches.append((i, best_j, best_sim))

        return matches


def process_tickers(
    companies_path: str = config.get("process.kg.tickers.input"),
    tickers_path: str = config.get("process.kg.tickers.cache"),
    output_path: str = config.get("process.kg.tickers.output"),
    url: str = config.get("process.kg.tickers.url"),
    threshold: float = 0.85,
    model_name: str = "intfloat/e5-base-v2",
    limit: int | None = None,
    download: bool = True,
    **kwargs: Any,  # Accept but ignore old BAML-related args
) -> int:
    """Process companies and match them with SEC tickers using embeddings.

    Uses embedding similarity to match company names from the knowledge graph
    with company names from SEC ticker data. Only matches above the similarity
    threshold are assigned.

    Args:
        companies_path: Path to companies.jsonl or companies.parquet
        tickers_path: Path to cache/load SEC tickers
        output_path: Path to write enriched companies
        url: URL to download SEC tickers from
        threshold: Minimum similarity threshold for a match (0-1)
        model_name: Embedding model to use
        limit: Maximum number of companies to process (for testing)
        download: Whether to download tickers from SEC (uses cache if exists)

    Returns:
        0 on success, 1 on failure
    """
    # Download SEC tickers if requested
    if download:
        tickers_path = download_sec_tickers(cache_path=tickers_path, url=url)

    # Load data
    companies_data = load_companies(companies_path)
    tickers_data = load_tickers(tickers_path)

    # Apply limit if specified
    if limit is not None:
        companies_data = companies_data[:limit]
        logger.info(f"Limited to {len(companies_data):,} companies")

    if not companies_data:
        logger.error("No companies to process")
        return 1

    if not tickers_data:
        logger.error("No tickers to process")
        return 1

    logger.info(f"Processing {len(companies_data):,} companies with {len(tickers_data):,} tickers")
    logger.info(f"Using similarity threshold: {threshold}")

    # Extract names
    company_names = [c.get("name", "") for c in companies_data]
    ticker_names = [t.get("name", "") for t in tickers_data]

    # Initialize matcher and find matches
    matcher = TickerMatcher(model_name=model_name)
    matches = matcher.find_matches(company_names, ticker_names, threshold=threshold)

    logger.info(f"Found {len(matches):,} matches above threshold {threshold}")

    # Build lookup from company index to ticker data
    match_lookup = {company_idx: (ticker_idx, sim) for company_idx, ticker_idx, sim in matches}

    # Enrich companies with matched tickers
    enriched_companies = []
    for i, company in tqdm(
        enumerate(companies_data), desc="Enriching companies", total=len(companies_data)
    ):
        enriched = company.copy()
        if i in match_lookup:
            ticker_idx, similarity = match_lookup[i]
            ticker_data = tickers_data[ticker_idx]
            enriched["ticker"] = {
                "symbol": ticker_data.get("symbol", ""),
                "name": ticker_data.get("name", ""),
                "exchange": ticker_data.get("exchange"),
                "cik": ticker_data.get("cik"),
            }
            enriched["ticker_similarity"] = similarity
            logger.debug(
                f"Matched '{company.get('name')}' -> '{ticker_data.get('name')}' "
                f"({ticker_data.get('symbol')}) with similarity {similarity:.3f}"
            )
        enriched_companies.append(enriched)

    # Count matches
    matched_count = len(matches)
    logger.info(
        f"Matched {matched_count:,} companies with tickers "
        f"({matched_count * 100 / len(companies_data):.1f}%)"
    )

    # Save results
    if save_jsonl(enriched_companies, output_path, create_backup=True):
        logger.info(f"Saved enriched companies to {output_path}")
    else:
        logger.error(f"Failed to save results to {output_path}")
        return 1

    return 0

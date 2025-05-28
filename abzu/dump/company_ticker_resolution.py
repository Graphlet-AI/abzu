"""Company ticker resolution dump command."""

import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests
from rapidfuzz import fuzz, process

from abzu.api.sec_downloader import HEADERS

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_TICKERS_CACHE = Path("data/sec/company_tickers.json")

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Normalize company names for comparison."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _load_sec_companies(cache_path: Path = SEC_COMPANY_TICKERS_CACHE) -> pd.DataFrame:
    """Load SEC company ticker list into a DataFrame with caching."""
    if cache_path.exists():
        with cache_path.open("r") as f:
            data = json.load(f)
    else:
        resp = requests.get(SEC_COMPANY_TICKERS_URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w") as f:
            json.dump(data, f)
    records = list(data.values()) if isinstance(data, dict) else data
    df = pd.DataFrame(records)
    df["_norm_title"] = df["title"].astype(str).apply(_normalize)
    return df


def _best_match(name: str, sec_map: Dict[str, str]) -> Tuple[str | None, float]:
    """Return best ticker match and score for a company name."""
    norm = _normalize(name)
    if norm in sec_map:
        return sec_map[norm], 1.0
    match = process.extractOne(norm, sec_map.keys(), scorer=fuzz.ratio)
    if not match:
        return None, 0.0
    match_norm, score, _ = match
    return sec_map[match_norm], score / 100


def dump_company_ticker_resolution_main(file_path: str) -> int:
    """Show proposed tickers for companies missing them."""
    try:
        companies_df = pd.read_parquet(file_path)
    except Exception as e:  # pragma: no cover - load failure
        logger.error(f"Failed to read companies file {file_path}: {e}")
        return 1

    try:
        sec_df = _load_sec_companies()
    except Exception as e:  # pragma: no cover - network issues
        logger.error(f"Failed to load SEC ticker list: {e}")
        return 1

    sec_map = dict(zip(sec_df["_norm_title"], sec_df["ticker"]))

    has_ticker = (
        companies_df["ticker"].notnull()
        if "ticker" in companies_df.columns
        else pd.Series([False] * len(companies_df))
    )

    no_ticker_df = companies_df[~has_ticker]

    header = f"{'Company':<40}{'Proposed':<15}{'Score':>6}"
    print(header)
    for _, row in no_ticker_df.iterrows():
        name = str(row.get("name", ""))
        proposed, score = _best_match(name, sec_map)
        score_pct = f"{score:.2f}"
        print(f"{name:<40}{(proposed or ''):<15}{score_pct:>6}")
    return 0

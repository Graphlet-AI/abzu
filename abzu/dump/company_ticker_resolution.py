"""Company ticker resolution dump command."""

import logging
import re
from difflib import SequenceMatcher
from typing import Tuple

import pandas as pd
import requests

from abzu.api.sec_downloader import HEADERS

SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Normalize company names for comparison."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _load_sec_companies() -> pd.DataFrame:
    """Load SEC company ticker list into a DataFrame."""
    resp = requests.get(SEC_COMPANY_TICKERS_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    records = list(data.values()) if isinstance(data, dict) else data
    df = pd.DataFrame(records)
    df["_norm_title"] = df["title"].astype(str).apply(_normalize)
    return df


def _best_match(name: str, sec_df: pd.DataFrame) -> Tuple[str | None, float]:
    """Return best ticker match and score for a company name."""
    norm = _normalize(name)
    best_score = 0.0
    best_ticker: str | None = None
    for _, row in sec_df.iterrows():
        score = SequenceMatcher(None, norm, row["_norm_title"]).ratio()
        if score > best_score:
            best_score = score
            best_ticker = row.get("ticker")
    return best_ticker, best_score


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
        proposed, score = _best_match(name, sec_df)
        score_pct = f"{score:.2f}"
        print(f"{name:<40}{(proposed or ''):<15}{score_pct:>6}")
    return 0

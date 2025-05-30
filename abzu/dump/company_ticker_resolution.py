"""Company ticker resolution dump command."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests
from cleanco import basename
from rapidfuzz import fuzz, process

from abzu.api.sec_downloader import HEADERS
from abzu.config import config

logger = logging.getLogger(__name__)


def _normalize(name: str) -> str:
    """Normalize company names for comparison."""
    base = basename(name)
    return re.sub(r"[^a-z0-9]", "", base.lower())


def _load_sec_companies(cache_path: Path = Path(config.get("dump.tickers.cache"))) -> pd.DataFrame:
    """Load SEC company ticker list into a DataFrame with caching."""
    if cache_path.exists():
        with cache_path.open("r") as f:
            data = json.load(f)
    else:
        resp = requests.get(config.get("dump.tickers.url"), headers=HEADERS, timeout=10)
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
    """Show proposed tickers for companies missing them.

    Any perfect match is written back to ``companies.parquet``.
    """
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

    if "ticker" not in companies_df.columns:
        companies_df["ticker"] = pd.NA

    updated = 0

    header = f"{'Company':<40}{'Proposed':<15}{'Score':>6}"
    print(header)
    for idx, row in no_ticker_df.iterrows():
        name = str(row.get("name", ""))
        proposed, score = _best_match(name, sec_map)
        score_pct = f"{score:.2f}"
        print(f"{name:<40}{(proposed or ''):<15}{score_pct:>6}")
        if proposed and score == 1.0:
            companies_df.loc[idx, "ticker"] = proposed  # type: ignore
            updated += 1

    if updated:
        try:
            companies_df.to_parquet(file_path, index=False)
        except Exception as e:  # pragma: no cover - write failure
            logger.error(f"Failed to update companies file {file_path}: {e}")
            return 1
        logger.info("Added %d ticker(s) to %s", updated, file_path)

    return 0

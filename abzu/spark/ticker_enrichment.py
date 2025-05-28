"""Helper functions for ticker enrichment during Spark processing."""

from typing import Dict

import pandas as pd

from abzu.dump.company_ticker_resolution import _best_match, _load_sec_companies


def load_sec_map() -> Dict[str, str]:
    """Return mapping of normalized company names to tickers from SEC data."""
    sec_df: pd.DataFrame = _load_sec_companies()
    return dict(zip(sec_df["_norm_title"], sec_df["ticker"]))


__all__ = ["_best_match", "load_sec_map"]

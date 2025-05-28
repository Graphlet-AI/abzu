import json
from pathlib import Path

import pandas as pd
import pytest

from abzu.dump.company_ticker_resolution import _best_match, _load_sec_companies


def test_load_sec_companies_from_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {"0": {"cik": 1, "title": "Alpha Inc", "ticker": "ALP"}}
    cache = tmp_path / "company_tickers.json"
    cache.write_text(json.dumps(sample))

    def fail_get(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr("requests.get", fail_get)
    df = _load_sec_companies(cache)
    assert df.loc[0, "ticker"] == "ALP"
    assert df.loc[0, "_norm_title"] == "alphainc"


def test_best_match(tmp_path: Path) -> None:
    data = pd.DataFrame(
        [{"title": "Alpha Inc", "ticker": "ALP"}, {"title": "Beta Co", "ticker": "BET"}]
    )
    data["_norm_title"] = data["title"].str.lower().str.replace("[^a-z0-9]", "", regex=True)
    sec_map = dict(zip(data["_norm_title"], data["ticker"]))

    ticker, score = _best_match("Alpha Inc", sec_map)
    assert ticker == "ALP"
    assert score == pytest.approx(1.0)

    ticker, score = _best_match("Alfa", sec_map)
    assert ticker == "ALP"
    assert score < 1.0

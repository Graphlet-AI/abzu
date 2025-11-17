import importlib
import json
from pathlib import Path

import pandas as pd
import pytest
from pyspark.sql import SparkSession

from abzu.dump.company_ticker_resolution import (
    _best_match,
    _load_sec_companies,
    _normalize,
    dump_company_ticker_resolution_main,
)
from abzu.spark.refine_kg import refine_knowledge_graph


def test_load_sec_companies_from_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {"0": {"cik": 1, "title": "Alpha Inc", "ticker": "ALP"}}
    cache = tmp_path / "company_tickers.json"
    cache.write_text(json.dumps(sample))

    def fail_get(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr("requests.get", fail_get)
    df = _load_sec_companies(cache)
    assert df.loc[0, "ticker"] == "ALP"
    assert df.loc[0, "_norm_title"] == "alpha"


def test_best_match(tmp_path: Path) -> None:
    data = pd.DataFrame(
        [{"title": "Alpha Inc", "ticker": "ALP"}, {"title": "Beta Co", "ticker": "BET"}]
    )
    data["_norm_title"] = data["title"].apply(_normalize)
    sec_map = dict(zip(data["_norm_title"], data["ticker"]))

    ticker, score = _best_match("Alpha Inc", sec_map)
    assert ticker == "ALP"
    assert score == pytest.approx(1.0)

    ticker, score = _best_match("Alfa", sec_map)
    assert ticker == "ALP"
    assert score < 1.0


@pytest.mark.skipif(importlib.util.find_spec("pyspark") is None, reason="PySpark not installed")
def test_refine_knowledge_graph_enriches_tickers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spark = SparkSession.builder.master("local[*]").appName("test").getOrCreate()

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    company_df = spark.createDataFrame([("Alpha Inc",), ("Beta Co",)], ["name"])
    company_df.write.parquet(str(input_dir / "companies.parquet"))

    product_df = spark.createDataFrame([], "name string")
    product_df.write.parquet(str(input_dir / "products.parquet"))
    technology_df = spark.createDataFrame([], "name string")
    technology_df.write.parquet(str(input_dir / "technologies.parquet"))

    ticker_df = spark.createDataFrame([(None, "BET", None)], ["name", "symbol", "exchange"])
    ticker_df.write.parquet(str(input_dir / "tickers.parquet"))

    company_ticker_df = spark.createDataFrame(
        [("Beta Co", "BET")], ["company_name", "ticker_symbol"]
    )
    company_ticker_df.write.parquet(str(input_dir / "company_ticker_relationships.parquet"))
    spark.createDataFrame([], "product_name string, company_name string").write.parquet(
        str(input_dir / "product_company_relationships.parquet")
    )
    spark.createDataFrame([], "technology_name string, company_name string").write.parquet(
        str(input_dir / "tech_company_relationships.parquet")
    )

    sec_df = pd.DataFrame([{"title": "Alpha Inc", "ticker": "ALP", "_norm_title": "alpha"}])
    monkeypatch.setattr("abzu.spark.ticker_enrichment._load_sec_companies", lambda: sec_df)

    refine_knowledge_graph(
        input_paths={"companies": str(input_dir / "companies.parquet")},
        output_paths={"tickers": str(output_dir / "tickers.parquet")},
        local_mode=True,
    )

    out_ticker_df = spark.read.parquet(str(output_dir / "tickers.parquet"))
    symbols = {row.symbol for row in out_ticker_df.collect()}
    assert symbols == {"BET", "ALP"}

    spark.stop()


def test_dump_company_ticker_resolution_writes_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    companies_df = pd.DataFrame(
        [
            {"name": "Alpha Inc"},
            {"name": "Beta Co", "ticker": "BET"},
        ]
    )
    file_path = tmp_path / "companies.parquet"
    companies_df.to_parquet(file_path, index=False)

    sec_df = pd.DataFrame([{"title": "Alpha Inc", "ticker": "ALP", "_norm_title": "alpha"}])
    monkeypatch.setattr("abzu.dump.company_ticker_resolution._load_sec_companies", lambda: sec_df)

    result = dump_company_ticker_resolution_main(str(file_path))
    assert result == 0

    out_df = pd.read_parquet(file_path)
    assert out_df.loc[out_df["name"] == "Alpha Inc", "ticker"].iat[0] == "ALP"
    assert out_df.loc[out_df["name"] == "Beta Co", "ticker"].iat[0] == "BET"

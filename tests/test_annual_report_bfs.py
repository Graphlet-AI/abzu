import json
from pathlib import Path

import pytest

from abzu.api import annual_report_processor as arp


def test_process_annual_reports_bfs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    processed: list[tuple[str, int]] = []

    def fake_process(ticker: str, year: int, output_dir: str) -> str:
        processed.append((ticker, year))
        data = {
            "reporting_company": {"name": ticker, "ticker": {"symbol": ticker}},
            "partnerships": [
                {
                    "company1": {"name": ticker, "ticker": {"symbol": ticker}},
                    "company2": {"name": "BBB", "ticker": {"symbol": "BBB"}},
                }
            ],
        }
        file_path = Path(output_dir) / f"{ticker}.json"
        file_path.write_text(json.dumps(data))
        return str(file_path)

    monkeypatch.setattr(arp, "process_annual_report", fake_process)
    monkeypatch.setattr(arp, "_latest_10k_year", lambda ticker: 2024)

    out = arp.process_annual_reports_bfs("AAA", 2023, str(tmp_path))

    assert set(out) == {"AAA", "BBB"}
    assert processed == [("AAA", 2023), ("BBB", 2024)]


def test_process_annual_reports_bfs_bulk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    processed: list[tuple[str, int]] = []

    def fake_process(ticker: str, year: int, output_dir: str) -> str:
        processed.append((ticker, year))
        if ticker == "AAA":
            partners = "BBB"
        elif ticker == "BBB":
            partners = "CCC"
        else:
            partners = None
        data = {
            "reporting_company": {"name": ticker, "ticker": {"symbol": ticker}},
            "partnerships": (
                [
                    {
                        "company1": {"name": ticker, "ticker": {"symbol": ticker}},
                        "company2": {"name": partners, "ticker": {"symbol": partners}},
                    }
                ]
                if partners
                else []
            ),
        }
        file_path = Path(output_dir) / f"{ticker}.json"
        file_path.write_text(json.dumps(data))
        return str(file_path)

    monkeypatch.setattr(arp, "process_annual_report", fake_process)
    monkeypatch.setattr(arp, "_latest_10k_year", lambda ticker: 2024)

    out = arp.process_annual_reports_bfs_bulk(["AAA", "CCC"], str(tmp_path))

    assert set(out) == {"AAA", "BBB", "CCC"}
    assert processed == [("AAA", 2024), ("CCC", 2024), ("BBB", 2024)]

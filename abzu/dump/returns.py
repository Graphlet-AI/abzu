import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_price_data(file_path: str) -> dict[str, Any]:
    """Load price data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def compute_returns(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute start and end prices along with percentage return."""
    results: list[dict[str, Any]] = []
    for symbol, record in data.items():
        if not isinstance(record, dict):
            continue
        if record.get("error"):
            continue
        prices = record.get("prices")
        if not isinstance(prices, list) or not prices:
            continue
        first = prices[0]
        last = prices[-1]
        try:
            start_price = float(first.get("close"))
            end_price = float(last.get("close"))
        except (TypeError, ValueError):
            continue
        if start_price == 0:
            continue
        return_pct = (end_price - start_price) / start_price * 100.0
        results.append(
            {
                "symbol": symbol,
                "start_price": start_price,
                "end_price": end_price,
                "return_pct": return_pct,
            }
        )
    results.sort(key=lambda x: x["return_pct"], reverse=True)
    return results


def dump_returns_main(file_path: str) -> int:
    """Load price file, compute returns, and print sorted results."""
    try:
        data = load_price_data(file_path)
    except Exception as e:  # pragma: no cover - load failure path
        logger.error(f"Failed to read prices file {file_path}: {e}")
        return 1

    results = compute_returns(data)

    header = f"{'Symbol':<10}{'Start':>12}{'End':>12}{'Return%':>10}"
    print(header)
    for item in results:
        print(
            f"{item['symbol']:<10}{item['start_price']:>12.2f}{item['end_price']:>12.2f}{item['return_pct']:>10.2f}"
        )
    return 0

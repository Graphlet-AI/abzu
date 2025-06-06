"""Build a Kuzu graph from processed annual report JSON files."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cleanco import basename

from abzu.logs import get_logger

logger = get_logger(__name__)


def _company_id(company: Dict[str, Any]) -> str:
    ticker = company.get("ticker")
    symbol: str | None = None
    if isinstance(ticker, dict):
        symbol = ticker.get("symbol")
    elif isinstance(ticker, str):
        symbol = ticker
    if symbol:
        return symbol.upper()

    # Use cleanco to create single-word ID from company name
    name = company.get("name", "").strip()
    if name:
        # Use cleanco to clean the company name
        cleaned = basename(name)
        # Remove all non-alphanumeric characters to create single word
        simplified = re.sub(r"[^a-zA-Z0-9]", "", cleaned)
        # If result is too short, fall back to processing original name
        if len(simplified) < 2:
            simplified = re.sub(r"[^a-zA-Z0-9]", "", name)
        return simplified
    return ""


def _add_company(companies: Dict[str, Dict[str, Optional[str]]], company: Dict[str, Any]) -> str:
    cid = _company_id(company)
    if not cid:
        return ""
    if cid not in companies:
        ticker_value = (
            company.get("ticker", {}).get("symbol")
            if isinstance(company.get("ticker"), dict)
            else company.get("ticker")
        )
        companies[cid] = {
            "id": cid,
            "name": company.get("name", "").strip(),
            "ticker": ticker_value if ticker_value else None,
        }
    return cid


def _process_file(
    path: Path, companies: Dict[str, Dict[str, Optional[str]]], edges: set[Tuple[str, str, str]]
) -> None:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reporting = data.get("reporting_company")
    if reporting:
        _add_company(companies, reporting)

    for part in data.get("partnerships", []) or []:
        c1 = part.get("company1")
        c2 = part.get("company2")
        if c1 and c2:
            id1 = _add_company(companies, c1)
            id2 = _add_company(companies, c2)
            if id1 and id2:
                edges.add((id1, id2, "partnership"))

    for inv in data.get("investments", []) or []:
        investor = inv.get("investor_company")
        invested = inv.get("invested_company")
        if investor and invested:
            id1 = _add_company(companies, investor)
            id2 = _add_company(companies, invested)
            if id1 and id2:
                edges.add((id1, id2, "investment"))

    for supplier in data.get("suppliers", []) or []:
        customer = supplier.get("customer_company")
        supplier_c = supplier.get("supplier_company")
        if customer and supplier_c:
            id1 = _add_company(companies, customer)
            id2 = _add_company(companies, supplier_c)
            if id1 and id2:
                edges.add((id1, id2, "supplier"))

    for sub in data.get("subsidiaries", []) or []:
        parent = sub.get("parent_company")
        name = sub.get("name")
        if parent and name:
            parent_id = _add_company(companies, parent)
            # Create simplified ID for subsidiary using cleanco
            sub_name = name.strip()
            if sub_name:
                cleaned = basename(sub_name)
                sub_id = re.sub(r"[^a-zA-Z0-9]", "", cleaned)
                if len(sub_id) < 2:
                    sub_id = re.sub(r"[^a-zA-Z0-9]", "", sub_name)
                if sub_id and sub_id not in companies:
                    companies[sub_id] = {"id": sub_id, "name": sub_name, "ticker": None}
                if parent_id:
                    edges.add((parent_id, sub_id, "subsidiary"))


def build_annual_report_kuzu_graph(input_dir: str, output_dir: str) -> Tuple[str, str]:
    """Extract relationships from processed annual reports and write CSV files.

    Parameters
    ----------
    input_dir:
        Directory containing processed annual report JSON files.
    output_dir:
        Directory where CSV files will be written.

    Returns
    -------
    Tuple[str, str]
        Paths to the companies and edges CSV files.
    """
    base = Path(input_dir)
    if not base.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    companies: Dict[str, Dict[str, Optional[str]]] = {}
    edges: set[Tuple[str, str, str]] = set()

    for file in base.rglob("processed_*.json"):
        try:
            _process_file(file, companies, edges)
        except Exception as exc:  # noqa: BLE001 - surface errors via log
            logger.error("Failed to process %s: %s", file, exc)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    companies_path = Path(output_dir) / "companies.csv"
    edges_path = Path(output_dir) / "edges.csv"

    with open(companies_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "ticker"])
        writer.writeheader()
        for comp in companies.values():
            writer.writerow(comp)

    with open(edges_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["src", "dst", "type"])
        writer.writeheader()
        for src, dst, rel in edges:
            writer.writerow({"src": src, "dst": dst, "type": rel})

    logger.info("Saved %d companies and %d edges", len(companies), len(edges))
    return str(companies_path), str(edges_path)

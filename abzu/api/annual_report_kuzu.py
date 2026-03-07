"""Build a Kuzu graph from processed annual report JSON files."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from cleanco import basename

from abzu.logs import get_logger

logger = get_logger(__name__)


def _company_id(company: dict[str, Any]) -> str:
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


def _add_company(companies: dict[str, dict[str, str | None]], company: dict[str, Any]) -> str:
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
    path: Path,
    companies: dict[str, dict[str, str | None]],
    invests_in: set[tuple[str, str]],
    has_investor: set[tuple[str, str]],
    partnered_with: set[tuple[str, str]],
    supplies: set[tuple[str, str]],
    has_supplier: set[tuple[str, str]],
    subsidiary_of: set[tuple[str, str]],
    has_subsidiary: set[tuple[str, str]],
) -> None:
    with open(path, encoding="utf-8") as f:
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
                partnered_with.add((id1, id2))
                partnered_with.add((id2, id1))

    for inv in data.get("investments", []) or []:
        investor = inv.get("investor_company")
        invested = inv.get("invested_company")
        if investor and invested:
            id1 = _add_company(companies, investor)
            id2 = _add_company(companies, invested)
            if id1 and id2:
                invests_in.add((id1, id2))
                has_investor.add((id2, id1))

    for supplier in data.get("suppliers", []) or []:
        customer = supplier.get("customer_company")
        vendor = supplier.get("supplier_company")
        if customer and vendor:
            cust_id = _add_company(companies, customer)
            vend_id = _add_company(companies, vendor)
            if cust_id and vend_id:
                supplies.add((vend_id, cust_id))
                has_supplier.add((cust_id, vend_id))

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
                    subsidiary_of.add((sub_id, parent_id))
                    has_subsidiary.add((parent_id, sub_id))


def build_annual_report_kuzu_graph(input_dir: str, output_dir: str) -> dict[str, str]:
    """Extract relationships from processed annual reports and write CSV files.

    Parameters
    ----------
    input_dir:
        Directory containing processed annual report JSON files.
    output_dir:
        Directory where CSV files will be written.

    Returns
    -------
    dict[str, str]
        Mapping of output CSV names to their file paths.
    """
    base = Path(input_dir)
    if not base.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    companies: dict[str, dict[str, str | None]] = {}
    invests_in: set[tuple[str, str]] = set()
    has_investor: set[tuple[str, str]] = set()
    partnered_with: set[tuple[str, str]] = set()
    supplies: set[tuple[str, str]] = set()
    has_supplier: set[tuple[str, str]] = set()
    subsidiary_of: set[tuple[str, str]] = set()
    has_subsidiary: set[tuple[str, str]] = set()

    for file in base.rglob("processed_*.json"):
        try:
            _process_file(
                file,
                companies,
                invests_in,
                has_investor,
                partnered_with,
                supplies,
                has_supplier,
                subsidiary_of,
                has_subsidiary,
            )
        except Exception as exc:  # noqa: BLE001 - surface errors via log
            logger.error("Failed to process %s: %s", file, exc)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    companies_path = Path(output_dir) / "companies.csv"
    invests_in_path = Path(output_dir) / "invests_in.csv"
    has_investor_path = Path(output_dir) / "has_investor.csv"
    partnered_with_path = Path(output_dir) / "partnered_with.csv"
    supplies_path = Path(output_dir) / "supplies.csv"
    has_supplier_path = Path(output_dir) / "has_supplier.csv"
    subsidiary_of_path = Path(output_dir) / "subsidiary_of.csv"
    has_subsidiary_path = Path(output_dir) / "has_subsidiary.csv"

    with open(companies_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "ticker"])
        writer.writeheader()
        for comp in companies.values():
            writer.writerow(comp)

    def _write_edges(path: Path, rows: Iterable[tuple[str, str]]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as edge_file:
            writer = csv.DictWriter(edge_file, fieldnames=["_from", "_to"])
            writer.writeheader()
            for src, dst in rows:
                writer.writerow({"_from": src, "_to": dst})

    _write_edges(invests_in_path, invests_in)
    _write_edges(has_investor_path, has_investor)
    _write_edges(partnered_with_path, partnered_with)
    _write_edges(supplies_path, supplies)
    _write_edges(has_supplier_path, has_supplier)
    _write_edges(subsidiary_of_path, subsidiary_of)
    _write_edges(has_subsidiary_path, has_subsidiary)
    logger.info(
        "Saved %d companies, %d invests_in, %d has_investor, %d partnered_with, %d supplies, %d has_supplier, %d subsidiary_of, %d has_subsidiary",
        len(companies),
        len(invests_in),
        len(has_investor),
        len(partnered_with),
        len(supplies),
        len(has_supplier),
        len(subsidiary_of),
        len(has_subsidiary),
    )
    return {
        "companies": str(companies_path),
        "invests_in": str(invests_in_path),
        "has_investor": str(has_investor_path),
        "partnered_with": str(partnered_with_path),
        "supplies": str(supplies_path),
        "has_supplier": str(has_supplier_path),
        "subsidiary_of": str(subsidiary_of_path),
        "has_subsidiary": str(has_subsidiary_path),
    }

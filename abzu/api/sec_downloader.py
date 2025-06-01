#!/usr/bin/env python3
# SEC XBRL Data Extractor - Revised  -- Trying to fix things

# Standard library imports
import json
import os
import re
import time
import traceback
from datetime import datetime  # timedelta was unused
from pathlib import Path
from typing import Any, Optional, cast

import pandas as pd
import requests
from bs4 import BeautifulSoup  # Tag was unused
from lxml import etree  # mypy: Unused "type: ignore" comment removed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from abzu.config import config

# Constants
USER_AGENT = "Your Name <youremail@example.com>"  # PLEASE REPLACE
HEADERS = {"User-Agent": USER_AGENT}
TICKER_URL = "https://www.sec.gov/include/ticker.txt"
BASE_JSON_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
BASE_ARCHIVES_URL = "https://www.sec.gov/Archives"
FACT_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"
COMPANY_CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:0>10}/us-gaap/{concept}.json"
)

# --- Robust session with retries ---
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# --- Centralized Concept Mapping ---
# This map defines the concepts we want to extract and the possible XBRL tags.
# The keys are our internal, standardized names for financial concepts.
# The values are lists of XBRL tags (us-gaap or dei) that could represent that concept.
CONCEPT_MAP: dict[str, list[str]] = {
    "EntityRegistrantName": ["dei:EntityRegistrantName"],
    "DocumentType": ["dei:DocumentType"],
    "DocumentPeriodEndDate": [
        "dei:DocumentPeriodEndDate",
        "us-gaap:DocumentPeriodEndDate",
        "us-gaap:BalanceSheetDate",
    ],
    "Assets": ["us-gaap:Assets"],
    "AssetsCurrent": ["us-gaap:AssetsCurrent"],
    "CashAndCashEquivalents": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
    "Liabilities": ["us-gaap:Liabilities"],
    "LiabilitiesCurrent": ["us-gaap:LiabilitiesCurrent"],
    "Equity": [
        "us-gaap:StockholdersEquity",
        "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "us-gaap:PartnersCapital",
    ],
    "Revenue": [
        "us-gaap:Revenues",
        "us-gaap:Revenue",
        "us-gaap:SalesRevenueNet",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
    "CostOfRevenue": ["us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsAndServicesSold"],
    "GrossProfit": ["us-gaap:GrossProfit"],
    "OperatingExpenses": ["us-gaap:OperatingExpenses"],
    "OperatingIncomeLoss": ["us-gaap:OperatingIncomeLoss"],
    "NetIncomeLoss": [
        "us-gaap:NetIncomeLoss",
        "us-gaap:ProfitLoss",
        "us-gaap:IncomeLossFromContinuingOperations",
    ],
    "EPSBasic": ["us-gaap:EarningsPerShareBasic"],
    "EPSDiluted": ["us-gaap:EarningsPerShareDiluted"],
    "CashFlowOperating": ["us-gaap:NetCashProvidedByUsedInOperatingActivities"],
    "CashFlowInvesting": ["us-gaap:NetCashProvidedByUsedInInvestingActivities"],
    "CashFlowFinancing": ["us-gaap:NetCashProvidedByUsedInFinancingActivities"],
    "CapEx": [
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        "us-gaap:CapitalExpenditures",
        "us-gaap:PurchaseOfPropertyPlantAndEquipment",
    ],
}


# --- Helper Functions ---
def parse_date_flexible(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parses a date string from various common formats into a datetime object.
    Returns None if parsing fails or input is None.
    """
    if not date_str:
        return None
    # Order matters: try more specific formats first if ambiguity exists,
    # but for these common ones, this order should be fine.
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # print(f"Warning: Could not parse date string: {date_str}") # Optional: for debugging
    return None


def get_cik_from_ticker(ticker: str) -> str:
    """
    Converts a stock ticker symbol to its corresponding CIK number using the SEC's ticker file.
    Raises KeyError if the ticker is not found.
    """
    print(f"Fetching CIK for ticker: {ticker} from {TICKER_URL}")
    resp = session.get(TICKER_URL, headers=HEADERS)
    resp.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
    for line in resp.text.splitlines():
        sym, cik_str = line.split("\t")
        if sym.lower() == ticker.lower():
            print(f"Found CIK: {cik_str} for ticker: {ticker}")
            return str(cik_str)  # CIK is returned as a string, potentially with leading zeros
    raise KeyError(f"Ticker {ticker} not found in SEC ticker list.")


def fetch_company_index(cik: str) -> dict[str, Any]:
    """
    Fetches the company submission index JSON from the SEC for a given CIK.
    This index contains metadata about all filings for the company.
    """
    url = BASE_JSON_URL.format(cik=cik)  # CIK should be zero-padded to 10 digits if not already
    print(f"Fetching company index for CIK {cik} from: {url}")
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    return cast(dict[str, Any], resp.json())  # Cast to satisfy mypy


def list_recent_filings(cik: str, form_type: str = "10-Q", count: int = 3) -> list[dict[str, Any]]:
    """
    Lists recent filings of a specific form type (e.g., "10-Q") for a given CIK.
    Returns a list of dictionaries, each containing details of a filing.
    """
    print(f"Listing recent {form_type} filings for CIK {cik}, count={count}")
    idx = fetch_company_index(cik)
    recent_filings_data = idx.get("filings", {}).get("recent", {})

    # Extract data for each relevant field
    accession_numbers = recent_filings_data.get("accessionNumber", [])
    primary_documents = recent_filings_data.get("primaryDocument", [])
    forms = recent_filings_data.get("form", [])
    filing_dates_str = recent_filings_data.get("filingDate", [])

    output_filings = []
    # Iterate safely up to the minimum length of the available data arrays
    num_entries = min(
        len(accession_numbers), len(primary_documents), len(forms), len(filing_dates_str)
    )

    for i in range(num_entries):
        acc = accession_numbers[i]
        doc = primary_documents[i]
        form = forms[i]
        date_str = filing_dates_str[i]

        if form == form_type:
            output_filings.append(
                {
                    "acc": acc.replace("-", ""),  # Accession number without dashes
                    "acc_with_dashes": acc,  # Accession number with dashes
                    "doc": doc,  # Primary document name (e.g., d430073d10q.htm)
                    "date": date_str,  # Filing date as string (YYYY-MM-DD)
                    "filing_date_obj": parse_date_flexible(date_str),  # Parsed datetime object
                }
            )
            if len(output_filings) >= count:
                break
    print(f"Found {len(output_filings)} recent {form_type} filings.")
    return output_filings


def get_xbrl_files(cik: str, accession: str) -> list[dict[str, Any]]:  # Return type changed
    """
    Finds XBRL-related files (XML, XBRL) associated with a specific filing.
    It tries to use the JSON index first, then falls back to HTML parsing of the directory.
    """
    acc_no_dashes = accession.replace("-", "")
    # Construct the base URL for the filing's directory on SEC Edgar
    filing_dir_url = f"{BASE_ARCHIVES_URL}/edgar/data/{int(cik)}/{acc_no_dashes}/"
    print(f"Searching for XBRL files in directory: {filing_dir_url}")

    xbrl_files: list[dict[str, Any]] = []  # Type changed to Any for values
    json_index_url = f"{filing_dir_url}index.json"  # Modern filings have a JSON index

    try:
        # Attempt to fetch and parse the JSON index
        resp = session.get(json_index_url, headers=HEADERS)
        resp.raise_for_status()
        index_data = resp.json()
        print(f"Successfully fetched JSON index: {json_index_url}")

        for file_entry in index_data.get("directory", {}).get("item", []):
            name = file_entry.get("name", "")
            # Filter for XML/XBRL files, excluding common linkbase roles and FilingSummary
            if (
                name.endswith((".xml", ".xbrl"))
                and not name.startswith("R")
                and not any(
                    suffix in name.lower()
                    for suffix in ["_cal.", "_def.", "_lab.", "_pre.", "filingsummary.xml"]
                )
            ):
                # Heuristic to identify instance documents: often end with _htm.xml or contain '-'
                is_instance = "_htm.xml" in name.lower() or (
                    "-" in name
                    and "." in name
                    and not any(
                        s in name.lower() for s in ["xsd", "_lab.", "_pre.", "_def.", "_cal."]
                    )
                )
                xbrl_files.append(
                    {
                        "name": name,
                        "url": f"{filing_dir_url}{name}",
                        "type": "xml" if name.endswith(".xml") else "xbrl",
                        "is_instance": is_instance,  # Boolean value
                    }
                )
    except (requests.RequestException, json.JSONDecodeError) as e:
        # Fallback to HTML parsing if JSON index is unavailable or invalid
        print(
            f"JSON index not available or failed to parse ({e}), falling back to HTML directory parsing for: {filing_dir_url}"
        )
        try:
            resp = session.get(filing_dir_url, headers=HEADERS)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.find_all("a", href=True):
                name = link.text.strip()
                if (
                    name.endswith((".xml", ".xbrl"))
                    and not name.startswith("R")
                    and not any(
                        suffix in name.lower()
                        for suffix in ["_cal.", "_def.", "_lab.", "_pre.", "filingsummary.xml"]
                    )
                ):
                    is_instance = "_htm.xml" in name.lower() or (
                        "-" in name
                        and "." in name
                        and not any(
                            s in name.lower() for s in ["xsd", "_lab.", "_pre.", "_def.", "_cal."]
                        )
                    )
                    xbrl_files.append(
                        {
                            "name": name,
                            "url": f"{filing_dir_url}{name}",  # Construct full URL
                            "type": "xml" if name.endswith(".xml") else "xbrl",
                            "is_instance": is_instance,  # Boolean value
                        }
                    )
        except requests.RequestException as html_e:
            print(f"Error fetching HTML directory {filing_dir_url}: {html_e}")

    # Sort files to prioritize likely instance documents
    xbrl_files.sort(
        key=lambda x: (not x["is_instance"], not x["name"].endswith("_htm.xml"), x["name"])
    )
    print(
        f"Found {len(xbrl_files)} potential XBRL-related files. Top candidates: {[f['name'] for f in xbrl_files[:3]]}"
    )
    return xbrl_files


def download_file(url: str, save_dir: str, file_name: str) -> str:
    """General utility to download a file and save it locally."""
    os.makedirs(save_dir, exist_ok=True)
    # Sanitize file_name to prevent directory traversal or invalid characters
    safe_file_name = re.sub(r"[^\w\.\-]", "_", file_name)
    local_path = os.path.join(save_dir, safe_file_name)

    print(f"Downloading {url} to {local_path}")
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(resp.content)
    time.sleep(
        0.2
    )  # Respect SEC rate limits (slightly reduced for potentially multiple small files)
    return local_path


def download_html_filing(
    cik: str, accession: str, primary_doc: str, save_dir: str = "filings"
) -> str:
    """Downloads the primary HTML document of a filing."""
    path = f"/edgar/data/{int(cik)}/{accession.replace('-', '')}/{primary_doc}"
    url = f"{BASE_ARCHIVES_URL}{path}"
    return download_file(url, save_dir, f"{cik}_{accession.replace('-', '')}_{primary_doc}")


def download_xbrl_file(file_info: dict[str, str], save_dir: str = "xbrl_files") -> str:
    """Downloads a specific XBRL-related file."""
    return download_file(file_info["url"], save_dir, file_info["name"])


def parse_xbrl_instance(file_path: str, filing_date_obj: datetime) -> dict[str, Any]:
    """
    Parses an XBRL instance file to extract contexts and facts based on CONCEPT_MAP.
    """
    print(f"Parsing XBRL file: {file_path}")
    try:
        # Use lxml.etree for robust XML parsing
        parser = etree.XMLParser(huge_tree=True, recover=True, no_network=True)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()

        # Consolidate namespaces, handling default namespace by assigning a prefix like 'def'
        nsmap = {k if k is not None else "def": v for k, v in root.nsmap.items()}

        contexts: dict[str, dict[str, Any]] = {}
        # XPath to find all context elements regardless of their specific namespace prefix
        for context_elem in root.xpath("//*[local-name()='context']"):
            context_id = context_elem.get("id")
            if not context_id:
                continue

            period_info: dict[str, str] = {}
            # Find period element within the current context
            period_elem = context_elem.find(".//*[local-name()='period']")
            if period_elem is not None:
                instant = period_elem.findtext(".//*[local-name()='instant']")
                startDate = period_elem.findtext(".//*[local-name()='startDate']")
                endDate = period_elem.findtext(".//*[local-name()='endDate']")
                if instant:
                    period_info["instant"] = instant.strip()
                if startDate:
                    period_info["startDate"] = startDate.strip()
                if endDate:
                    period_info["endDate"] = endDate.strip()

            dimensions: dict[str, str] = {}
            # Find segment element for dimensional information
            segment_elem = context_elem.find(".//*[local-name()='segment']")
            if segment_elem is not None:
                for member in segment_elem.xpath(".//*[local-name()='explicitMember']"):
                    dim = member.get("dimension")
                    val = member.text
                    if dim and val:
                        dimensions[dim.strip()] = val.strip()
            contexts[context_id] = {"period": period_info, "dimensions": dimensions}

        if not contexts:
            return {"error": "No contexts found in XBRL document."}
        print(f"Found {len(contexts)} contexts in XBRL.")

        facts: dict[str, list[dict[str, Any]]] = {}
        raw_fact_count = 0
        # Iterate through our defined concepts and their corresponding XBRL tags
        for concept_key, xbrl_tags_for_concept in CONCEPT_MAP.items():
            for xbrl_tag in xbrl_tags_for_concept:
                ns_prefix, local_name = xbrl_tag.split(":")

                elements: list[Any]  # Declare type for elements
                # Construct XPath query using the namespace prefix found in the document
                xpath_query = f"//{ns_prefix}:{local_name}"
                # If the prefix isn't in the doc's nsmap but 'def' (default) is, try that
                if (
                    ns_prefix not in nsmap
                    and "def" in nsmap
                    and nsmap["def"] == nsmap.get(ns_prefix)
                ):
                    elements = root.xpath(f"//def:{local_name}", namespaces=nsmap)
                elif ns_prefix not in nsmap:
                    elements = root.xpath(f"//*[local-name()='{local_name}']")
                else:
                    elements = root.xpath(xpath_query, namespaces=nsmap)

                for elem in elements:
                    raw_fact_count += 1
                    context_ref = elem.get("contextRef")
                    unit_ref = elem.get("unitRef")
                    decimals = elem.get("decimals")
                    value_str = elem.text

                    if value_str and context_ref and context_ref in contexts:
                        value: Any = None
                        try:
                            # Attempt to convert to float, handling potential errors
                            value = float(value_str.strip())
                        except ValueError:
                            value = (
                                value_str.strip()
                            )  # Keep as string if not floatable (e.g., for text facts)

                        if concept_key not in facts:
                            facts[concept_key] = []

                        facts[concept_key].append(
                            {
                                "value": value,
                                "context_id": context_ref,  # Store context ID for later linking
                                "unit": unit_ref,
                                "decimals": decimals,
                                "xbrl_tag": xbrl_tag,  # Store which specific XBRL tag this fact came from
                            }
                        )

        print(
            f"Processed {raw_fact_count} raw fact elements, mapped to {len(facts)} distinct concepts."
        )
        if not facts:
            return {"error": "No facts matching CONCEPT_MAP were found in XBRL."}

        return {"contexts": contexts, "facts": facts}

    except etree.XMLSyntaxError as e:
        print(f"XML Syntax Error parsing XBRL {file_path}: {str(e)}")
        return {"error": f"XML Syntax Error: {str(e)}"}
    except Exception as e:
        print(f"Generic exception parsing XBRL {file_path}: {str(e)}")
        traceback.print_exc()
        return {"error": f"Failed to parse XBRL: {str(e)}"}


def find_best_quarter_end_date(
    xbrl_data: dict[str, Any], filing_date_obj: datetime
) -> Optional[str]:
    """
    Determines the most relevant quarter end date from parsed XBRL data.
    Prioritizes 'DocumentPeriodEndDate' facts and validates against the filing date.
    """
    if "error" in xbrl_data or "facts" not in xbrl_data or "contexts" not in xbrl_data:
        print("Cannot determine quarter end date: XBRL data is invalid or incomplete.")
        return None

    potential_dates: set[str] = set()

    # 1. Try 'DocumentPeriodEndDate' facts first
    doc_period_end_facts = xbrl_data["facts"].get("DocumentPeriodEndDate", [])
    for fact in doc_period_end_facts:
        if isinstance(fact.get("value"), str):
            date_val_str = fact["value"]
            dt_obj = parse_date_flexible(date_val_str)
            # Validate: date must be before filing date and reasonably close (e.g., within 150 days)
            if dt_obj and dt_obj < filing_date_obj and (filing_date_obj - dt_obj).days <= 150:
                potential_dates.add(date_val_str)

    # 2. If not found or not suitable, infer from context end dates of major financial facts
    if not potential_dates:
        print(
            "No direct 'DocumentPeriodEndDate' fact found or suitable. Inferring from other key facts."
        )
        key_concepts_for_date_inference = ["Assets", "NetIncomeLoss", "Revenue"]
        for concept_key in key_concepts_for_date_inference:
            if concept_key in xbrl_data["facts"]:
                for fact in xbrl_data["facts"][concept_key]:
                    context = xbrl_data["contexts"].get(fact["context_id"], {})
                    period = context.get("period", {})
                    # Prefer 'endDate' for durations, 'instant' for point-in-time
                    end_date_str = period.get("endDate") or period.get("instant")
                    if end_date_str:
                        dt_obj = parse_date_flexible(end_date_str)
                        if (
                            dt_obj
                            and dt_obj < filing_date_obj
                            and (filing_date_obj - dt_obj).days <= 150
                        ):
                            potential_dates.add(end_date_str)

    if not potential_dates:
        print("Could not determine a reliable recent quarter_end_date from XBRL contexts.")
        return None

    # Sort potential dates and pick the latest valid one
    # Ensure dates are valid datetime objects for sorting before converting back to string
    valid_datetime_objects = [
        d for d in [parse_date_flexible(s) for s in potential_dates] if d is not None
    ]
    if not valid_datetime_objects:
        print("No valid datetime objects found from potential dates.")
        return None

    sorted_dates_obj = sorted(valid_datetime_objects, reverse=True)

    if sorted_dates_obj:
        best_date_str = sorted_dates_obj[0].strftime("%Y-%m-%d")
        print(f"Determined best quarter_end_date from XBRL: {best_date_str}")
        return best_date_str
    print("No suitable quarter end dates found after sorting.")
    return None


def extract_relevant_facts_for_period(
    xbrl_data: dict[str, Any], target_quarter_end_date: str
) -> dict[str, Any]:
    """
    Extracts facts that match the target_quarter_end_date.
    Prioritizes facts with no dimensions (assumed to be consolidated/primary figures).
    """
    if "error" in xbrl_data or not target_quarter_end_date:
        return {
            "error": xbrl_data.get("error", "Missing target_quarter_end_date or invalid XBRL data.")
        }

    output_facts: dict[str, dict[str, Any]] = {}
    contexts = xbrl_data.get("contexts", {})

    for concept_key, fact_list in xbrl_data.get("facts", {}).items():
        best_fact_for_concept: Optional[dict[str, Any]] = None
        for fact_data in fact_list:
            context_id = fact_data["context_id"]
            context = contexts.get(context_id)
            if not context:
                continue

            period = context.get("period", {})
            fact_date_str = period.get("endDate") or period.get("instant")

            if fact_date_str == target_quarter_end_date:
                # If this fact matches the target date
                current_fact_details = {
                    "value": fact_data["value"],
                    "unit": fact_data["unit"],
                    "xbrl_tag": fact_data["xbrl_tag"],
                }
                # Prioritize facts with no dimensions (consolidated figures)
                if not context.get("dimensions"):
                    best_fact_for_concept = current_fact_details
                    break  # Found the best (non-dimensional) fact for this concept and period
                elif best_fact_for_concept is None:
                    # If no non-dimensional fact found yet, take the first dimensional one encountered
                    best_fact_for_concept = current_fact_details

        if best_fact_for_concept:
            output_facts[concept_key] = best_fact_for_concept

    if not output_facts:
        print(
            f"No facts extracted for target period {target_quarter_end_date}. This might be okay if the period had no data for mapped concepts."
        )
    return output_facts


def get_data_from_sec_api(
    cik: str,
    api_type: str,
    concept_name_map: Optional[dict[str, list[str]]] = None,
    min_filing_year: int = 0,
) -> dict[str, Any]:
    """
    Fetches and processes data from SEC's CompanyFacts or CompanyConcept API.
    - api_type: "facts" or "concept".
    - concept_name_map: For "concept" API, maps our internal concept name to a list of SEC concept names.
                      For "facts" API, uses CONCEPT_MAP by default.
    - min_filing_year: Minimum filing year for facts to be considered recent (e.g., 2023).
    """
    results: dict[str, Any] = {"data": {}, "errors": [], "metadata": {}}
    current_year = datetime.now().year
    if not min_filing_year:  # Default to last 2 full years + current year
        min_filing_year = current_year - 2

    # Determine which map to use for concepts
    active_concept_map = (
        concept_name_map if api_type == "concept" and concept_name_map else CONCEPT_MAP
    )

    if api_type == "facts":
        url = FACT_URL.format(cik=cik.zfill(10))  # Ensure CIK is 10 digits, zero-padded
        print(f"Fetching from SEC CompanyFacts API: {url}")
        try:
            resp = session.get(url, headers=HEADERS)
            resp.raise_for_status()
            api_data = resp.json()
        except requests.RequestException as e:
            results["errors"].append(f"CompanyFacts API request failed: {e}")
            return results
        except json.JSONDecodeError as e:
            results["errors"].append(f"CompanyFacts API JSON decode failed: {e}")
            return results

        results["metadata"]["entityName"] = api_data.get("entityName")
        results["metadata"]["cik"] = api_data.get("cik")

        for our_concept, xbrl_tags in active_concept_map.items():
            found_concept_data = False
            for xbrl_tag in xbrl_tags:  # Try each XBRL tag for our concept
                # Extract the base concept name (e.g., "Assets" from "us-gaap:Assets")
                gaap_concept_name = xbrl_tag.split(":")[-1]
                concept_data_block = (
                    api_data.get("facts", {}).get("us-gaap", {}).get(gaap_concept_name)
                )

                if concept_data_block and "units" in concept_data_block:
                    for unit, values_list in concept_data_block.get("units", {}).items():
                        # Filter for 10-Q forms, recent filing dates, and sort by end date (most recent first)
                        quarterly_values_temp = []
                        for v_item in values_list:
                            if v_item.get("form") == "10-Q":
                                filed_date_obj = parse_date_flexible(v_item.get("filed"))
                                if filed_date_obj and filed_date_obj.year >= min_filing_year:
                                    quarterly_values_temp.append(v_item)
                        quarterly_values = quarterly_values_temp
                        quarterly_values.sort(key=lambda x: x.get("end", ""), reverse=True)

                        if quarterly_values:
                            latest_q_fact = quarterly_values[0]  # Get the most recent one
                            results["data"][our_concept] = {
                                "value": latest_q_fact.get("val"),
                                "unit": unit,
                                "endDate": latest_q_fact.get("end"),
                                "filingDate": latest_q_fact.get("filed"),
                                "xbrl_tag": xbrl_tag,  # Store which tag provided this data
                            }
                            # Attempt to set a document period end date from a major concept if not already set
                            if (
                                our_concept in ["Assets", "Revenue", "NetIncomeLoss"]
                                and not results["metadata"].get("documentPeriodEndDate")
                                and latest_q_fact.get("end")
                            ):
                                results["metadata"]["documentPeriodEndDate"] = latest_q_fact.get(
                                    "end"
                                )
                            found_concept_data = True
                            break  # Found data for this xbrl_tag, move to next our_concept
                    if found_concept_data:
                        break  # Found data for our_concept, move to next our_concept
            if not found_concept_data:
                results["data"][our_concept] = None  # Explicitly mark as None if no data found

    elif (
        api_type == "concept" and concept_name_map
    ):  # Ensure concept_name_map is provided for 'concept' type
        for our_concept, sec_concept_list in concept_name_map.items():
            found_concept_data_api = False
            for (
                sec_concept_name
            ) in (
                sec_concept_list
            ):  # e.g., "Revenues" or "PaymentsToAcquirePropertyPlantAndEquipment"
                url = COMPANY_CONCEPT_URL.format(cik=cik.zfill(10), concept=sec_concept_name)
                print(
                    f"Fetching from SEC CompanyConcept API for '{our_concept}' (using '{sec_concept_name}'): {url}"
                )
                try:
                    resp = session.get(url, headers=HEADERS)
                    resp.raise_for_status()
                    api_data = resp.json()
                except requests.RequestException as e:
                    print(f"CompanyConcept API for '{sec_concept_name}' failed: {e}")
                    continue  # Try next SEC concept name in the list
                except json.JSONDecodeError as e:
                    print(f"CompanyConcept API JSON decode for '{sec_concept_name}' failed: {e}")
                    continue

                if "units" in api_data:  # Check if the API returned any data for this concept
                    for unit, values_list in api_data.get("units", {}).items():
                        quarterly_values_temp = []
                        for v_item in values_list:
                            if v_item.get("form") == "10-Q":
                                filed_date_obj = parse_date_flexible(v_item.get("filed"))
                                if filed_date_obj and filed_date_obj.year >= min_filing_year:
                                    quarterly_values_temp.append(v_item)
                        quarterly_values = quarterly_values_temp
                        quarterly_values.sort(key=lambda x: x.get("end", ""), reverse=True)

                        if quarterly_values:
                            latest_q_fact = quarterly_values[0]
                            results["data"][our_concept] = {
                                "value": latest_q_fact.get("val"),
                                "unit": unit,
                                "endDate": latest_q_fact.get("end"),
                                "filingDate": latest_q_fact.get("filed"),
                                "xbrl_tag": f"us-gaap:{sec_concept_name}",  # Reconstruct an approximate tag
                            }
                            if (
                                our_concept in ["Assets", "Revenue", "NetIncomeLoss"]
                                and not results["metadata"].get("documentPeriodEndDate")
                                and latest_q_fact.get("end")
                            ):
                                results["metadata"]["documentPeriodEndDate"] = latest_q_fact.get(
                                    "end"
                                )
                            found_concept_data_api = True
                            break  # Found data for this unit, move to next our_concept
                    if found_concept_data_api:
                        break  # Found data for this sec_concept_name, move to next our_concept
            if not found_concept_data_api:
                results["data"][our_concept] = None
    else:
        results["errors"].append(
            f"Invalid API type ('{api_type}') or missing concept_name_map for type 'concept'."
        )

    return results


def extract_from_html(html_path: str, filing_date_obj: datetime) -> dict[str, Any]:
    """
    Extracts basic financial data from an HTML filing as a last resort.
    This is highly heuristic and less reliable than XBRL or API methods.
    """
    print(f"Attempting to extract data from HTML (last resort): {html_path}")
    # Initialize all mapped concepts to None for this HTML extraction attempt
    financial_data: dict[str, Any] = {key: None for key in CONCEPT_MAP.keys()}
    financial_data["source_method"] = "html_extraction_WARN"  # Mark as HTML sourced with a warning

    try:
        with open(html_path, "rb") as f:  # Open in binary read mode
            soup = BeautifulSoup(f, "html.parser")
    except Exception as e:
        print(f"Error reading or parsing HTML file {html_path}: {e}")
        financial_data["error_html_parsing"] = str(e)
        return financial_data

    # 1. Try to find DocumentPeriodEndDate from HTML content
    possible_dates: list[datetime] = []
    # Regex to find common date phrases and then extract dates
    date_text_patterns = re.compile(
        r"(period end|as of|ended|for the quarter ended|for the three months ended)", re.I
    )
    date_value_patterns = re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b"  # Month D, YYYY
        r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"  # M/D/YY or M/D/YYYY
        r"|\b\d{4}-\d{2}-\d{2}\b"  # YYYY-MM-DD
    )

    # Search all text nodes for date-related phrases
    text_nodes = soup.find_all(string=True)
    for node in text_nodes:
        node_text = str(node).strip()
        if date_text_patterns.search(node_text):
            # If a date phrase is found, search for actual date values in the vicinity (parent element)
            parent_context_text = (
                node.parent.get_text(separator=" ", strip=True) if node.parent else node_text
            )
            date_matches = date_value_patterns.findall(parent_context_text)
            for date_str_match in date_matches:
                dt_obj = parse_date_flexible(date_str_match)
                # Validate: date must be before filing date and reasonably close
                if (
                    dt_obj and dt_obj < filing_date_obj and (filing_date_obj - dt_obj).days <= 180
                ):  # Slightly wider window for HTML
                    possible_dates.append(dt_obj)

    if possible_dates:
        best_date_obj = max(possible_dates)  # Get the latest valid date found
        financial_data["DocumentPeriodEndDate"] = best_date_obj.strftime("%Y-%m-%d")
        print(
            f"HTML: Determined DocumentPeriodEndDate (approx): {financial_data['DocumentPeriodEndDate']}"
        )
    else:
        print("HTML: Could not reliably determine DocumentPeriodEndDate from text.")

    # 2. Try to find other financial values using keywords in tables
    html_keywords_map: dict[str, list[str]] = {
        "Revenue": ["revenue", "net sales", "total net sales", "total revenues"],
        "NetIncomeLoss": [
            "net income",
            "net earnings",
            "net (loss) income",
            "net loss attributable",
            "net income attributable",
        ],
        "Assets": ["total assets"],
        "Liabilities": ["total liabilities"],
        "Equity": [
            "total stockholders' equity",
            "total equity",
            "shareholders' equity",
            "total deficit",
        ],
        "CapEx": [
            "capital expenditure",
            "payments for property",
            "additions to property",
            "purchase of property",
        ],
    }

    tables = soup.find_all("table")

    print(f"HTML: Found {len(tables)} tables to scan.")
    for table_idx, table in enumerate(tables):
        # Check for "in thousands" or "in millions" in table headers or nearby text
        multiplier = 1
        # Look in a limited region around the table for unit indicators
        table_context_text = ""
        # Iterate a few parents up or siblings back to find unit text
        current_element_for_context: Any = table
        for _ in range(3):  # Check up to 3 levels of parents
            if current_element_for_context and current_element_for_context.parent:
                table_context_text += current_element_for_context.parent.get_text(
                    separator=" ", strip=True
                ).lower()
                current_element_for_context = current_element_for_context.parent
            else:
                break

        if not table_context_text:  # If parent search failed, just use table's own text
            table_context_text = table.get_text(separator=" ", strip=True).lower()

        if (
            "in thousands" in table_context_text
            and "in millions" not in table_context_text
            and "in billions" not in table_context_text
        ):
            multiplier = 1000
        elif "in millions" in table_context_text and "in billions" not in table_context_text:
            multiplier = 1000000
        elif "in billions" in table_context_text:
            multiplier = 1000000000
        if multiplier > 1:
            print(f"HTML Table {table_idx}: Detected multiplier {multiplier}")

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:  # Need at least a label and a value cell
                continue

            row_label = cells[0].get_text(strip=True).lower()
            # Try to get value from the last few cells, preferring the rightmost numeric one
            numeric_value: Optional[float] = None
            for cell_idx in range(len(cells) - 1, 0, -1):  # Iterate backwards from last cell
                row_value_text = cells[cell_idx].get_text(strip=True)
                # Clean value: remove currency, commas; handle parentheses for negatives
                cleaned_value_text = row_value_text.replace("$", "").replace(",", "")
                if "(" in cleaned_value_text and ")" in cleaned_value_text:
                    cleaned_value_text = "-" + cleaned_value_text.replace("(", "").replace(")", "")

                if not cleaned_value_text or cleaned_value_text in [
                    "—",
                    "-",
                ]:  # Skip if empty or just a dash
                    continue
                try:
                    numeric_value = float(cleaned_value_text) * multiplier
                    break  # Found a numeric value
                except ValueError:
                    continue  # Not a floatable value in this cell

            if numeric_value is not None:
                for concept_key, keywords_list in html_keywords_map.items():
                    if financial_data.get(concept_key) is None:  # Only if not already found by HTML
                        for kw in keywords_list:
                            # Use regex for more flexible keyword matching (e.g., whole word)
                            if re.search(r"\b" + re.escape(kw) + r"\b", row_label, re.IGNORECASE):
                                financial_data[concept_key] = {
                                    "value": numeric_value,
                                    "unit": "USD_HTML_ESTIMATE",
                                    "xbrl_tag": "N/A_HTML",
                                }
                                print(
                                    f"HTML: Found {concept_key} ('{kw}' in '{row_label}'): {numeric_value}"
                                )
                                break  # Keyword found for this concept, move to next concept_key
                    if (
                        financial_data.get(concept_key) is not None and kw in keywords_list
                    ):  # break outer loop if concept filled
                        break
    return financial_data


def process_10q_filing(ticker: str, filing_idx: int = 0) -> dict[str, Any]:
    """
    Main orchestrator to process a 10-Q filing.
    It tries multiple methods: SEC APIs, XBRL parsing, and HTML parsing as a fallback.
    """
    try:
        cik = get_cik_from_ticker(ticker)
        print(f"\n=== Processing {ticker} (CIK: {cik}), Filing Index: {filing_idx} ===")

        filings = list_recent_filings(cik, form_type="10-Q", count=filing_idx + 1)
        if not filings or filing_idx >= len(filings):
            return {
                "error": f"No 10-Q filing found at index {filing_idx} for {ticker}",
                "ticker": ticker,
                "cik": cik,
            }

        filing_info = filings[filing_idx]
        filing_date_str = filing_info["date"]
        filing_date_obj = filing_info["filing_date_obj"]
        accession_no = filing_info["acc_with_dashes"]
        primary_doc_name = filing_info["doc"]

        if not filing_date_obj:  # Should not happen if list_recent_filings works
            return {
                "error": f"Could not parse filing date for {accession_no}",
                "ticker": ticker,
                "cik": cik,
            }

        print(
            f"Target Filing: Accession# {accession_no}, Filed: {filing_date_str}, Primary Doc: {primary_doc_name}"
        )

        final_results: dict[str, Any] = {
            "ticker": ticker,
            "cik": cik,
            "filing_date": filing_date_str,
            "accession_number": accession_no,
            "source_method": "N/A",
            "financial_data": {
                key: None for key in CONCEPT_MAP.keys()
            },  # Initialize all concepts to None
            "errors": [],
        }

        # --- Method 1: SEC CompanyFacts API ---
        print("\n--- Attempt 1: SEC CompanyFacts API ---")
        api_facts_result = get_data_from_sec_api(
            cik, "facts", min_filing_year=filing_date_obj.year - 2
        )  # Look back ~2 years from filing year

        if not api_facts_result.get("errors") and api_facts_result.get("data"):
            api_doc_end_date_str = api_facts_result.get("metadata", {}).get("documentPeriodEndDate")
            api_doc_end_date_obj = parse_date_flexible(api_doc_end_date_str)

            # Validate API's period end date against the actual filing date
            if (
                api_doc_end_date_obj
                and api_doc_end_date_obj < filing_date_obj
                and (filing_date_obj - api_doc_end_date_obj).days <= 150
            ):  # Period end date is reasonably close
                final_results["source_method"] = "sec_company_facts_api"
                final_results["financial_data"]["DocumentPeriodEndDate"] = api_doc_end_date_str
                populated_count = 0
                for concept, data_val in api_facts_result["data"].items():
                    if data_val:
                        final_results["financial_data"][concept] = data_val
                        populated_count += 1
                print(
                    f"CompanyFacts API: Successfully extracted {populated_count} concepts for period ending {api_doc_end_date_str}."
                )
                # If key data points are found, we might consider this sufficient
                key_items_found = sum(
                    1
                    for k in ["Revenue", "NetIncomeLoss", "Assets", "CapEx"]
                    if final_results["financial_data"].get(k)
                )
                if key_items_found >= 3:  # If we found 3 of the 4 main items
                    print("CompanyFacts API provided sufficient key data. Finalizing.")
                    return final_results
                else:
                    print(
                        f"CompanyFacts API data was sparse ({key_items_found} key items). Will try other methods."
                    )
            else:
                final_results["errors"].append(
                    f"CompanyFacts API DocumentPeriodEndDate ({api_doc_end_date_str}) not suitable for filing {filing_date_str}."
                )
                print(
                    f"CompanyFacts API DocumentPeriodEndDate ({api_doc_end_date_str}) not suitable for filing {filing_date_str}."
                )
        else:
            final_results["errors"].extend(
                api_facts_result.get("errors", ["Unknown error with CompanyFacts API."])
            )
            print(
                f"CompanyFacts API failed or returned no data. Errors: {api_facts_result.get('errors')}"
            )

        # --- Method 2: XBRL File Parsing ---
        print("\n--- Attempt 2: XBRL File Parsing ---")
        xbrl_files_list = get_xbrl_files(cik, accession_no)
        if not xbrl_files_list:
            final_results["errors"].append("No XBRL files found for parsing.")
            print("No XBRL files found to parse.")
        else:
            parsed_xbrl_data: Optional[dict[str, Any]] = None
            target_xbrl_doc_end_date: Optional[str] = None
            best_xbrl_file_source_name: Optional[str] = None

            for xbrl_file_info in xbrl_files_list:  # Already sorted by likelihood of being instance
                print(
                    f"Attempting to parse XBRL file: {xbrl_file_info['name']} (Marked as instance: {xbrl_file_info.get('is_instance', False)})"
                )
                # Define save directory for XBRL files to avoid clutter
                xbrl_save_dir = os.path.join(
                    config.get("api.sec.download.xbrl_files"), cik, accession_no.replace("-", "")
                )
                file_path = download_xbrl_file(xbrl_file_info, save_dir=xbrl_save_dir)

                _current_parsed_data = parse_xbrl_instance(file_path, filing_date_obj)
                if "error" not in _current_parsed_data and _current_parsed_data.get("facts"):
                    _current_doc_end_date = find_best_quarter_end_date(
                        _current_parsed_data, filing_date_obj
                    )
                    if _current_doc_end_date:
                        # This XBRL file yielded a valid period end date
                        parsed_xbrl_data = _current_parsed_data
                        target_xbrl_doc_end_date = _current_doc_end_date
                        best_xbrl_file_source_name = xbrl_file_info["name"]
                        print(
                            f"Successfully parsed XBRL and found valid period: {target_xbrl_doc_end_date} from {best_xbrl_file_source_name}"
                        )
                        break  # Found a good XBRL file and its period, stop searching
                    else:
                        print(
                            f"Parsed {xbrl_file_info['name']}, but could not determine a valid recent period end date."
                        )
                else:
                    print(
                        f"Failed to parse or find facts in {xbrl_file_info['name']}. Error: {_current_parsed_data.get('error')}"
                    )

            if parsed_xbrl_data and target_xbrl_doc_end_date:
                xbrl_extracted_facts = extract_relevant_facts_for_period(
                    parsed_xbrl_data, target_xbrl_doc_end_date
                )
                if "error" not in xbrl_extracted_facts and xbrl_extracted_facts:
                    # Merge XBRL data, potentially overwriting API data if XBRL is deemed more direct for the filing
                    final_results["source_method"] = (
                        f"xbrl_file_parsing ({best_xbrl_file_source_name})"
                    )
                    final_results["financial_data"][
                        "DocumentPeriodEndDate"
                    ] = target_xbrl_doc_end_date
                    populated_count = 0
                    for concept, data_val in xbrl_extracted_facts.items():
                        if data_val:
                            final_results["financial_data"][concept] = data_val
                            populated_count += 1
                    print(
                        f"XBRL Parsing: Successfully extracted {populated_count} concepts for period ending {target_xbrl_doc_end_date}."
                    )
                    # Check if XBRL provided enough key data
                    key_items_found_xbrl = sum(
                        1
                        for k in ["Revenue", "NetIncomeLoss", "Assets", "CapEx"]
                        if final_results["financial_data"].get(k)
                    )
                    if key_items_found_xbrl >= 3:
                        print("XBRL parsing provided sufficient key data. Finalizing.")
                        return final_results
                    else:
                        print(
                            f"XBRL data was sparse ({key_items_found_xbrl} key items). May fall back to HTML if needed."
                        )
                else:
                    error_msg = f"Failed to extract relevant facts for period {target_xbrl_doc_end_date} from parsed XBRL. Error: {xbrl_extracted_facts.get('error')}"
                    final_results["errors"].append(error_msg)
                    print(error_msg)
            else:
                final_results["errors"].append(
                    "Could not find/parse a suitable XBRL instance document or determine its period."
                )
                print("XBRL Parsing: No suitable instance document found or period determined.")

        # --- Method 3: HTML Filing Extraction (Last Resort or Supplement) ---
        # Only run if primary methods didn't yield enough, or to fill gaps.
        should_try_html = True
        if final_results["source_method"] != "N/A":
            key_items_from_primary = sum(
                1
                for k in ["Revenue", "NetIncomeLoss", "Assets", "CapEx"]
                if final_results["financial_data"].get(k)
            )
            if key_items_from_primary >= 2:  # If we already have 2+ key items, maybe skip HTML
                print(
                    "\nPrimary methods yielded some key data. Skipping HTML unless gaps are large."
                )
                # should_try_html = False # Uncomment to be less reliant on HTML

        if should_try_html:
            print("\n--- Attempt 3: HTML Filing Extraction (Fallback/Supplement) ---")
            try:
                html_save_dir = os.path.join(
                    config.get("api.sec.download.html_filings"), cik, accession_no.replace("-", "")
                )
                html_path = download_html_filing(
                    cik, accession_no, primary_doc_name, save_dir=html_save_dir
                )
                html_extracted_data = extract_from_html(html_path, filing_date_obj)

                html_doc_end_date_str = html_extracted_data.get("DocumentPeriodEndDate")

                # If HTML found a date and no other method established one, or if HTML's date is better
                if (
                    html_doc_end_date_str
                    and final_results["financial_data"].get("DocumentPeriodEndDate") is None
                ):
                    final_results["financial_data"]["DocumentPeriodEndDate"] = html_doc_end_date_str
                    if final_results["source_method"] == "N/A":  # If no method worked yet
                        final_results["source_method"] = "html_extraction_WARN (primary)"
                    print(f"HTML: Set DocumentPeriodEndDate to {html_doc_end_date_str}")

                # Fill in missing data from HTML if other methods didn't find it
                html_filled_count = 0
                for concept, html_val in html_extracted_data.items():
                    if (
                        concept
                        not in ["source_method", "error_html_parsing", "DocumentPeriodEndDate"]
                        and html_val
                        and final_results["financial_data"].get(concept) is None
                    ):
                        final_results["financial_data"][concept] = html_val
                        html_filled_count += 1

                if html_filled_count > 0:
                    print(f"HTML: Supplemented {html_filled_count} missing concepts.")
                    if not final_results["source_method"].startswith(
                        "html_extraction_WARN (primary)"
                    ):
                        if final_results["source_method"] == "N/A":
                            final_results["source_method"] = "html_extraction_WARN (supplement)"
                        elif "WARN" not in final_results["source_method"]:
                            final_results[
                                "source_method"
                            ] += " +html_supplement_WARN"  # Added space

                if "error_html_parsing" in html_extracted_data:
                    final_results["errors"].append(
                        f"HTML parsing error: {html_extracted_data['error_html_parsing']}"
                    )

            except Exception as e:
                error_msg = f"HTML processing failed: {str(e)}"
                final_results["errors"].append(error_msg)
                print(error_msg)
                traceback.print_exc()

        if final_results["source_method"] == "N/A":
            final_results["errors"].append(
                "Failed to extract significant data using any reliable method."
            )
            print("CRITICAL: Failed to extract significant data using any method.")

        return final_results

    except KeyError as e:  # e.g. Ticker not found
        print(f"KeyError during processing for {ticker}: {str(e)}")
        return {"error": str(e), "ticker": ticker}
    except requests.exceptions.RequestException as e:
        print(f"Network error during processing for {ticker}: {str(e)}")
        return {"error": f"Network error: {str(e)}", "ticker": ticker}
    except Exception as e:
        print(f"Unexpected critical error processing {ticker}: {str(e)}")
        traceback.print_exc()
        return {"error": f"Unexpected critical error: {str(e)}", "ticker": ticker}


def save_results_to_json(data: dict[str, Any], output_file: str = "10q_data.json"):
    """Saves the extracted data dictionary to a JSON file."""
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        # Use default=str to handle any non-serializable objects like datetime
        json.dump(data, f, indent=2, default=str)
    print(f"Results successfully saved to {output_file}")


def display_financial_summary(results: dict[str, Any]):
    """Prints a formatted summary of the extracted financial data."""

    ticker = results.get("ticker", "N/A")
    if "error" in results and not results.get(
        "financial_data"
    ):  # Critical error before data structure init
        print(f"\n--- Error Summary for {ticker} ---")
        print(f"Error: {results['error']}")
        return

    print(f"\n--- Financial Summary for {ticker} ---")
    print(f"CIK: {results.get('cik', 'N/A')}")
    print(f"Filing Date: {results.get('filing_date', 'N/A')}")
    print(f"Accession Number: {results.get('accession_number', 'N/A')}")
    print(f"Data Source Method(s): {results.get('source_method', 'N/A')}")

    financial_data = results.get("financial_data", {})
    doc_period_end_val = financial_data.get("DocumentPeriodEndDate")

    # Handle DocumentPeriodEndDate which might be a string or a dict from API/XBRL
    if isinstance(doc_period_end_val, dict) and "value" in doc_period_end_val:
        print(f"Document Period End Date: {doc_period_end_val['value']}")
    elif isinstance(doc_period_end_val, str):
        print(f"Document Period End Date: {doc_period_end_val}")
    else:
        # Corrected f-string: removed f if no placeholder
        print("Document Period End Date: Not reliably determined or N/A")

    if results.get("errors"):
        print("\nEncountered Errors/Warnings:")
        for err_idx, err in enumerate(results["errors"][:5]):  # Print first 5 errors/warnings
            print(f"  - {err_idx + 1}: {err}")  # Added space around +
        if len(results["errors"]) > 5:
            print(f"  ... and {len(results['errors']) - 5} more.")

    print("\nKey Financial Data Points:")
    # Iterate through CONCEPT_MAP to display in a consistent order
    for concept_key in CONCEPT_MAP.keys():
        if concept_key == "DocumentPeriodEndDate":
            continue  # Already handled

        data_item = financial_data.get(concept_key)

        if data_item and isinstance(data_item, dict):  # Fact structure from API or XBRL
            value = data_item.get("value", "N/A")
            unit = data_item.get("unit", "")
            xbrl_tag_info = (
                f"(Source Tag: {data_item.get('xbrl_tag', 'N/A')})"
                if data_item.get("xbrl_tag")
                else ""
            )

            value_str = str(value)  # Default to string
            if isinstance(value, (int, float)):
                try:  # Format numeric values nicely
                    value_str = (
                        f"${value:,.0f}" if unit and "USD" in str(unit).upper() else f"{value:,.0f}"
                    )
                except (ValueError, TypeError):
                    pass  # Keep as string if formatting fails

            print(f"  {concept_key:<25}: {value_str:<15} {unit:<10} {xbrl_tag_info}")
        elif (
            data_item is None and concept_key != "source_method"
        ):  # Explicitly show None for unpopulated mapped concepts
            print(f"  {concept_key:<25}: None")
        # Else: data_item might be a simple string (e.g. from HTML DocumentPeriodEndDate, already handled) or other non-dict type


def process_all_tickers(
    tickers_file: str = config.get("api.sec.download.tickers_file"),
    output_dir: str = config.get("api.sec.download.output_dir"),
    filing_index: int = 0,
) -> None:
    """Process 10-Q filings for all tickers in a Parquet file."""

    print("Reading tickers file", tickers_file)

    df = pd.read_parquet(tickers_file)
    tickers = df["symbol"].dropna().unique()

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        print(f"Processing ticker: {ticker}")
        result = process_10q_filing(ticker, filing_idx=filing_index)

        accession = result.get("accession_number", "UNKNOWN_ACC").replace("-", "")
        fname = f"{ticker}_{accession}_10q_data.json"
        save_results_to_json(result, os.path.join(output_dir, fname))

        display_financial_summary(result)


if __name__ == "__main__":
    process_all_tickers()

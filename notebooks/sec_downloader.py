#!/usr/bin/env python3
# SEC XBRL Data Extractor

import json

# Standard library imports
import os
import time
from datetime import datetime
from typing import Any, Dict, List

# Third-party library imports
import requests
from bs4 import BeautifulSoup, Tag
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
USER_AGENT = "Your Name <youremail@example.com>"
HEADERS = {"User-Agent": USER_AGENT}
TICKER_URL = "https://www.sec.gov/include/ticker.txt"
BASE_JSON_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
BASE_ARCHIVES_URL = "https://www.sec.gov/Archives"
FACT_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"
COMPANY_CONCEPT_URL = (
    "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik:0>10}/us-gaap/{concept}.json"
)

# ——— robust session with retries ———
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def get_cik_from_ticker(ticker: str) -> str:
    """Convert a stock ticker to a CIK number."""
    resp = session.get(TICKER_URL, headers=HEADERS)
    resp.raise_for_status()
    for line in resp.text.splitlines():
        sym, cik = line.split("\t")
        if sym.lower() == ticker.lower():
            return cik
    raise KeyError(f"Ticker {ticker} not found")


def fetch_company_index(cik: str) -> Any:
    """Fetch the company submission index from SEC."""
    url = BASE_JSON_URL.format(cik=cik)
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def list_recent_filings(cik: str, form_type: str = "10-Q", count: int = 3) -> list:
    """List recent filings of a specific form type."""
    idx = fetch_company_index(cik)
    recent = idx["filings"]["recent"]

    # now pull out accession, primaryDocument, form, date
    entries = zip(
        recent["accessionNumber"], recent["primaryDocument"], recent["form"], recent["filingDate"]
    )

    out = []
    for acc, doc, form, date in entries:
        if form == form_type:
            out.append(
                {"acc": acc.replace("-", ""), "acc_with_dashes": acc, "doc": doc, "date": date}
            )
            if len(out) >= count:
                break
    return out


def get_xbrl_files(cik: str, accession: str) -> List[Dict[str, str]]:
    """Find XBRL files associated with a specific filing."""
    # Format the URL to the filing directory
    acc_no_dashes = accession.replace("-", "")
    url = f"{BASE_ARCHIVES_URL}/edgar/data/{int(cik)}/{acc_no_dashes}/"

    print(f"Searching for XBRL files in: {url}")

    # Get the index file
    index_url = f"{url}/index.json"
    try:
        resp = session.get(index_url, headers=HEADERS)
        resp.raise_for_status()
        index_data = resp.json()

        # Extract file info from index
        xbrl_files = []
        for file_entry in index_data.get("directory", {}).get("item", []):
            name = file_entry.get("name", "")
            # Exclude calculation, definition, label, and presentation linkbases
            if not name.startswith("R") and name.endswith((".xml", ".xbrl")):
                xbrl_files.append(
                    {
                        "name": name,
                        "url": f"{url}/{name}",
                        "type": "xml" if name.endswith(".xml") else "xbrl",
                        "is_instance": not any(
                            suffix in name.lower()
                            for suffix in ["_cal.", "_def.", "_lab.", "_pre."]
                        ),
                    }
                )
        return xbrl_files
    except requests.RequestException as e:
        print(f"JSON index not available: {str(e)}")
        # Fallback to HTML parsing if JSON index not available
        resp = session.get(url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        xbrl_files = []
        for link in soup.find_all("a"):
            name = link.text.strip()
            # Exclude calculation, definition, label, and presentation linkbases
            if not name.startswith("R") and name.endswith((".xml", ".xbrl")):
                xbrl_files.append(
                    {
                        "name": name,
                        "url": f"{url}/{name}",
                        "type": "xml" if name.endswith(".xml") else "xbrl",
                        "is_instance": not any(
                            suffix in name.lower()
                            for suffix in ["_cal.", "_def.", "_lab.", "_pre."]
                        ),
                    }
                )
        return xbrl_files


def download_xbrl_file(file_info: Dict[str, str], save_dir: str = "xbrl_files") -> str:
    """Download an XBRL file and save it locally."""
    os.makedirs(save_dir, exist_ok=True)
    url = file_info["url"]
    file_name = file_info["name"]

    print(f"Downloading {url}")

    # Create a unique filename
    local_path = os.path.join(save_dir, file_name)

    # Download the file
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()

    with open(local_path, "wb") as f:
        f.write(resp.content)

    time.sleep(1)  # Respect SEC rate limits
    return local_path


def download_html_filing(
    cik: str, accession: str, primary_doc: str, save_dir: str = "filings"
) -> str:
    """Download the HTML version of a filing."""
    os.makedirs(save_dir, exist_ok=True)
    path = f"/edgar/data/{int(cik)}/{accession.replace('-', '')}/{primary_doc}"
    url = f"{BASE_ARCHIVES_URL}{path}"

    print(f"Downloading HTML filing: {url}")

    # Download the file
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()

    # Save to disk
    fn = os.path.join(save_dir, f"{cik}_{accession.replace('-', '')}.html")
    with open(fn, "wb") as f:
        f.write(resp.content)

    time.sleep(1)  # Respect SEC rate limits
    return fn


def parse_xbrl_instance(file_path: str) -> Dict[str, Any]:
    """
    Parse an XBRL instance file and extract key financial data.
    Returns a dictionary of concept names mapped to their values.
    """
    print(f"Parsing XBRL file: {file_path}")

    # Read the file content
    with open(file_path, "rb") as f:
        content = f.read()

    # Check if file is empty or too small
    if len(content) < 100:
        return {"error": "File is empty or too small to be valid XBRL"}

    # Check if this is a FilingSummary.xml, which is not an XBRL instance
    if "FilingSummary" in file_path and b"<FilingSummary>" in content[:1000]:
        return {"error": "FilingSummary.xml is not an XBRL instance document"}

    # Print first 500 bytes for debugging
    content_preview = content[:500].decode("utf-8", errors="replace")
    print(f"File content preview: {content_preview}")

    try:
        # Parse the XML file
        parser = etree.XMLParser(huge_tree=True, recover=True)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()

        # Identify all namespaces used in the file
        nsmap = root.nsmap
        print(f"Detected namespaces: {nsmap}")

        # Create a namespace map that doesn't include the default namespace (None key)
        # This is needed because XPath doesn't support default namespaces
        xpath_nsmap = {k: v for k, v in nsmap.items() if k is not None}

        # Add xbrli namespace if not present but we have the default namespace pointing to XBRL
        if "xbrli" not in xpath_nsmap and None in nsmap and "xbrl.org/2003/instance" in nsmap[None]:
            xpath_nsmap["xbrli"] = nsmap[None]

        # Extract the context elements using safer approach
        contexts = {}

        # First try with explicit xbrli namespace
        if "xbrli" in xpath_nsmap:
            try:
                context_elements = root.xpath("//xbrli:context", namespaces=xpath_nsmap)
                print(f"Found {len(context_elements)} contexts with xbrli namespace")
            except Exception as e:
                print(f"Error finding contexts with xbrli namespace: {str(e)}")
                context_elements = []
        else:
            context_elements = []

        # If that fails, try finding contexts by local name
        if not context_elements:
            try:
                # Try finding all elements with local name "context"
                context_elements = root.xpath("//*[local-name()='context']")
                print(f"Found {len(context_elements)} contexts using local-name")
            except Exception as e:
                print(f"Error finding contexts with local-name: {str(e)}")
                context_elements = []

        for context in context_elements:
            context_id = context.get("id")
            if context_id:
                # Get period information using local-name() approach
                period_elem = None
                try:
                    period_elems = context.xpath(".//*[local-name()='period']")
                    if period_elems:
                        period_elem = period_elems[0]
                except Exception as e:
                    print(f"Error finding period element: {str(e)}")

                if period_elem is not None:
                    instant = None
                    start_date = None
                    end_date = None

                    try:
                        instant_elems = period_elem.xpath(".//*[local-name()='instant']")
                        if instant_elems and instant_elems[0].text:
                            instant = instant_elems[0].text
                    except Exception:
                        pass

                    try:
                        start_date_elems = period_elem.xpath(".//*[local-name()='startDate']")
                        if start_date_elems and start_date_elems[0].text:
                            start_date = start_date_elems[0].text
                    except Exception:
                        pass

                    try:
                        end_date_elems = period_elem.xpath(".//*[local-name()='endDate']")
                        if end_date_elems and end_date_elems[0].text:
                            end_date = end_date_elems[0].text
                    except Exception:
                        pass

                    period_info = {}
                    if instant:
                        period_info["instant"] = instant
                    if start_date:
                        period_info["startDate"] = start_date
                    if end_date:
                        period_info["endDate"] = end_date

                    # Check for segment/dimension information
                    dimensions = {}
                    try:
                        segment_elems = context.xpath(".//*[local-name()='segment']")
                        if segment_elems:
                            segment = segment_elems[0]
                            for dim in segment.xpath(".//*[local-name()='explicitMember']"):
                                dimension = dim.get("dimension")
                                value = dim.text
                                if dimension and value:
                                    dimensions[dimension] = value
                    except Exception:
                        pass

                    contexts[context_id] = {"period": period_info, "dimensions": dimensions}

        # Count contexts for debugging
        print(f"Found {len(contexts)} contexts")

        if len(contexts) == 0:
            return {"error": "No contexts found in the XBRL document"}

        # Extract facts (data points)
        facts: Dict[str, List[Dict[str, Any]]] = {}
        fact_count = 0

        # Get all elements to search for facts
        all_elements = []

        try:
            # First try to get all elements
            all_elements = root.xpath("//*")
            print(f"Found {len(all_elements)} total elements in the document")
        except Exception as e:
            print(f"Error getting all elements: {str(e)}")
            return {"error": f"Failed to extract elements: {str(e)}"}

        # Process each element to find facts
        for elem in all_elements:
            # Check if this element has a namespace
            elem_tag = elem.tag
            if "}" in elem_tag:
                ns_uri, local_name = elem_tag.split("}", 1)
                ns_uri = ns_uri[1:]  # Remove the opening '{'

                # Find the prefix for this namespace URI
                prefix = None
                for pre, uri in nsmap.items():
                    if uri == ns_uri and pre is not None:
                        prefix = pre
                        break

                if prefix and prefix.lower() in ["us-gaap", "dei", "ifrs"]:
                    # This is a financial concept
                    concept = f"{prefix}:{local_name}"
                    context_ref = elem.get("contextRef")
                    unit_ref = elem.get("unitRef")
                    decimals = elem.get("decimals")
                    value = elem.text

                    if value and context_ref and context_ref in contexts:
                        # Clean and convert value if numeric
                        try:
                            if value.strip():
                                numeric_value = float(value)
                            else:
                                numeric_value = None
                        except ValueError:
                            numeric_value = value

                        # Create a unique key for this fact
                        fact_key = concept

                        # Store the fact with its context
                        if fact_key not in facts:
                            facts[fact_key] = []

                        facts[fact_key].append(
                            {
                                "value": numeric_value,
                                "context": contexts[context_ref],
                                "unit": unit_ref,
                                "decimals": decimals,
                            }
                        )
                        fact_count += 1

        print(f"Extracted {fact_count} facts across {len(facts)} concepts")

        if fact_count == 0:
            # This might not be an instance document, but a linkbase
            print("No facts found. This may be a linkbase file, not an XBRL instance document.")
            return {"error": "No facts found in file - likely not an XBRL instance document"}

        return {"contexts": contexts, "facts": facts}

    except Exception as e:
        print(f"Exception parsing XBRL: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": f"Failed to parse XBRL: {str(e)}"}


def get_quarterly_facts(
    facts: Dict[str, List[Dict[str, Any]]], quarter_end_date: str
) -> Dict[str, Any]:
    """
    Extract facts that match a specific quarter end date.

    Args:
        facts: Dictionary of facts from parse_xbrl_instance
        quarter_end_date: ISO format date string (YYYY-MM-DD)

    Returns:
        Dictionary of concepts with their values for the specified quarter
    """
    quarterly_data: Dict[str, Any] = {}

    for concept, fact_list in facts.items():
        for fact in fact_list:
            # Check for end date in context period
            period = fact.get("context", {}).get("period", {})
            context_end_date = period.get("endDate") or period.get("instant")

            # If this fact is for our target quarter
            if context_end_date == quarter_end_date:
                # Skip if it has dimensions (we want the primary items)
                dimensions = fact.get("context", {}).get("dimensions", {})
                if not dimensions:
                    quarterly_data[concept] = {"value": fact["value"], "unit": fact["unit"]}

    return quarterly_data


def extract_financial_statements(xbrl_data: Dict[str, Any], filing_date: str) -> Dict[str, Any]:
    """
    Extract key financial statements from XBRL data.

    Args:
        xbrl_data: Dictionary from parse_xbrl_instance
        filing_date: The filing date in ISO format (YYYY-MM-DD)

    Returns:
        Dictionary with balance sheet, income statement, and cash flow data
    """
    # Check if we have an error
    if "error" in xbrl_data:
        return {"error": xbrl_data["error"]}

    # Check if we have facts
    if not xbrl_data.get("facts"):
        return {"error": "No facts found in XBRL data"}

    # Find the most recent quarter end date
    quarter_end_dates = set()

    # Look for key date indicators in different ways
    date_indicators = [
        "dei:DocumentPeriodEndDate",
        "us-gaap:DocumentPeriodEndDate",
        "us-gaap:BalanceSheetDate",
        "us-gaap:StatementOfIncomeAndComprehensiveIncomeStatementPeriodYearToDateEndDate",
    ]

    # First try to get document period end date directly
    for indicator in date_indicators:
        if indicator in xbrl_data["facts"]:
            for fact in xbrl_data["facts"][indicator]:
                if fact.get("value"):
                    if isinstance(fact["value"], str):
                        quarter_end_dates.add(fact["value"])
                    else:
                        # Try to get it from context
                        period = fact.get("context", {}).get("period", {})
                        end_date = period.get("endDate") or period.get("instant")
                        if end_date:
                            quarter_end_dates.add(end_date)

    # If no direct date indicators, try inferring from contexts of common financial concepts
    if not quarter_end_dates:
        print("No direct date indicators found, inferring from contexts...")
        for concept_name in xbrl_data["facts"]:
            if any(
                item in concept_name.lower()
                for item in ["revenue", "assets", "liabilities", "netincome"]
            ):
                for fact in xbrl_data["facts"][concept_name]:
                    period = fact.get("context", {}).get("period", {})
                    end_date = period.get("endDate")
                    if end_date and end_date < filing_date:  # Ensure it's before filing date
                        quarter_end_dates.add(end_date)

    print(f"Possible quarter end dates: {quarter_end_dates}")

    # Use the most recent quarter end date
    if quarter_end_dates:
        quarter_end_date = max(quarter_end_dates)
        print(f"Selected quarter end date: {quarter_end_date}")
    else:
        # Fallback strategy if no clear quarter end date
        return {"error": "Could not determine quarter end date"}

    # Extract facts for this quarter
    quarterly_facts = get_quarterly_facts(xbrl_data["facts"], quarter_end_date)

    if not quarterly_facts:
        print("No quarterly facts found, trying context-based selection...")
        # Try using shortest period that includes the quarter end date
        contexts_by_length = []
        for concept, fact_list in xbrl_data["facts"].items():
            if concept.lower().startswith(("us-gaap:", "ifrs:")):
                for fact in fact_list:
                    period = fact.get("context", {}).get("period", {})
                    start_date = period.get("startDate")
                    end_date = period.get("endDate") or period.get("instant")

                    if end_date and start_date:
                        # Calculate period length
                        try:
                            end = datetime.fromisoformat(end_date)
                            start = datetime.fromisoformat(start_date)
                            length = (end - start).days

                            # If period includes our target date and is less than a year
                            if end_date == quarter_end_date and length <= 365:
                                contexts_by_length.append((length, fact))
                        except Exception as e:
                            print(f"Error calculating period length: {e}")

        # Sort by period length
        contexts_by_length.sort()

        # Extract facts from the shortest contexts
        if contexts_by_length:
            # Get the shortest period length
            min_length = contexts_by_length[0][0]

            # Get all facts with this period length
            for length, fact in contexts_by_length:
                if length == min_length:
                    concept = None
                    for c, facts in xbrl_data["facts"].items():
                        if fact in facts:
                            concept = c
                            break

                    if concept:
                        quarterly_facts[concept] = {"value": fact["value"], "unit": fact["unit"]}

    # Organize data into financial statements
    balance_sheet = {}
    income_statement = {}
    cash_flow = {}

    # Common financial statement items to extract - expand this list as needed
    bs_items = [
        "us-gaap:Assets",
        "us-gaap:AssetsCurrent",
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:Liabilities",
        "us-gaap:LiabilitiesCurrent",
        "us-gaap:StockholdersEquity",
        "us-gaap:AccountsReceivableNetCurrent",
        "us-gaap:Inventory",
        "us-gaap:PropertyPlantAndEquipmentNet",
        "us-gaap:IntangibleAssetsNetExcludingGoodwill",
        "us-gaap:Goodwill",
        "us-gaap:LongTermDebt",
        "us-gaap:RetainedEarnings",
    ]

    is_items = [
        "us-gaap:Revenues",
        "us-gaap:Revenue",
        "us-gaap:SalesRevenueNet",
        "us-gaap:CostOfRevenue",
        "us-gaap:GrossProfit",
        "us-gaap:OperatingExpenses",
        "us-gaap:OperatingIncomeLoss",
        "us-gaap:IncomeTaxExpenseBenefit",
        "us-gaap:NetIncomeLoss",
        "us-gaap:EarningsPerShareBasic",
        "us-gaap:EarningsPerShareDiluted",
    ]

    cf_items = [
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "us-gaap:NetCashProvidedByUsedInInvestingActivities",
        "us-gaap:NetCashProvidedByUsedInFinancingActivities",
        "us-gaap:CashAndCashEquivalentsPeriodIncreaseDecrease",
    ]

    # Extract balance sheet items
    for item in bs_items:
        if item in quarterly_facts:
            balance_sheet[item.split(":")[-1]] = quarterly_facts[item]

    # Extract income statement items
    for item in is_items:
        if item in quarterly_facts:
            income_statement[item.split(":")[-1]] = quarterly_facts[item]

    # Extract cash flow items
    for item in cf_items:
        if item in quarterly_facts:
            cash_flow[item.split(":")[-1]] = quarterly_facts[item]

    # Look for additional items with related names
    for concept in quarterly_facts:
        concept_name = concept.lower()

        # Check for potential balance sheet items
        if any(
            term in concept_name
            for term in [
                "asset",
                "liability",
                "equity",
                "debt",
                "receivable",
                "inventory",
                "payable",
            ]
        ):
            if concept not in bs_items:
                balance_sheet[concept.split(":")[-1]] = quarterly_facts[concept]

        # Check for potential income statement items
        elif any(
            term in concept_name
            for term in ["revenue", "income", "earning", "profit", "expense", "cost", "tax", "eps"]
        ):
            if concept not in is_items:
                income_statement[concept.split(":")[-1]] = quarterly_facts[concept]

        # Check for potential cash flow items
        elif any(term in concept_name for term in ["cash", "financing", "investing", "operating"]):
            if concept not in cf_items:
                cash_flow[concept.split(":")[-1]] = quarterly_facts[concept]

    return {
        "quarter_end_date": quarter_end_date,
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "cash_flow": cash_flow,
        "fact_count": len(quarterly_facts),
    }


def get_facts_from_sec_api(cik: str) -> Dict[str, Any]:
    """
    Get company facts directly from the SEC's API.
    This is an alternative approach that uses the SEC's structured data API.

    Args:
        cik: Company CIK number

    Returns:
        Dictionary with company facts data
    """
    url = FACT_URL.format(cik=cik.zfill(10))
    print(f"Fetching facts from SEC API: {url}")
    try:
        resp = session.get(url, headers=HEADERS)
        resp.raise_for_status()
        result: Dict[str, Any] = resp.json()
        return result
    except requests.RequestException as e:
        print(f"Error fetching facts from SEC API: {str(e)}")
        error_dict: Dict[str, Any] = {"error": f"Failed to fetch facts: {str(e)}"}
        return error_dict


def extract_from_facts(facts_data: Dict[str, Any], concept_list: List[str]) -> Dict[str, Any]:
    """
    Extract data for a specific concept from the SEC Facts API response.

    Args:
        facts_data: The response from the SEC Facts API
        concept_list: List of concept names to try (will use first one found)

    Returns:
        Dictionary with quarterly values
    """
    # Check for errors in facts_data
    if "error" in facts_data:
        return {
            "concept": concept_list[0] if concept_list else "unknown",
            "error": facts_data["error"],
            "quarterly_data": [],
        }

    # Print the available concepts for debugging
    if "facts" in facts_data and "us-gaap" in facts_data["facts"]:
        available_concepts = list(facts_data["facts"]["us-gaap"].keys())
        print(
            f"Available US-GAAP concepts ({len(available_concepts)}): {available_concepts[:10]}..."
        )
    else:
        print("No US-GAAP concepts found in facts data")
        if "facts" in facts_data:
            print(f"Available fact categories: {list(facts_data['facts'].keys())}")

    # Try each concept in the list
    for concept in concept_list:
        # Check if this concept exists in the facts
        if (
            "facts" in facts_data
            and "us-gaap" in facts_data["facts"]
            and concept in facts_data["facts"]["us-gaap"]
        ):
            concept_data = facts_data["facts"]["us-gaap"][concept]

            # Get the units (usually USD)
            units = list(concept_data.get("units", {}).keys())
            if not units:
                continue

            unit = units[0]  # Usually 'USD'
            values = concept_data["units"][unit]

            # Filter for 10-Q filings and sort by end date (most recent first)
            quarterly_values = [v for v in values if v.get("form") == "10-Q"]
            quarterly_values.sort(key=lambda x: x.get("end", ""), reverse=True)

            # Format into our standard output
            quarterly_data = []
            for i, value in enumerate(quarterly_values[:4]):  # Get up to 4 quarters
                quarterly_data.append(
                    {
                        "end_date": value.get("end"),
                        "value": value.get("val"),
                        "filing_date": value.get("filed"),
                    }
                )

                # Calculate quarter-over-quarter changes
                if i > 0 and quarterly_data[i - 1]["value"] and quarterly_data[i]["value"]:
                    current = quarterly_data[i - 1]["value"]
                    previous = quarterly_data[i]["value"]

                    if previous != 0:
                        pct_change = ((current - previous) / abs(previous)) * 100
                        quarterly_data[i - 1]["pct_change_from_previous"] = pct_change

            return {"concept": concept, "quarterly_data": quarterly_data}

    # Search for similar concepts using pattern matching
    if "facts" in facts_data and "us-gaap" in facts_data["facts"]:
        # Define pattern matches based on the concept we're looking for
        patterns: Dict[str, List[str]] = {
            "us-gaap:Revenues": ["revenue", "sales", "turnover"],
            "us-gaap:Revenue": ["revenue", "sales", "turnover"],
            "us-gaap:NetIncomeLoss": ["netincome", "earnings", "profit", "loss"],
            "us-gaap:Assets": ["totalasset", "asset"],
            "us-gaap:Liabilities": ["totalliabilit", "liabilit"],
            "us-gaap:StockholdersEquity": ["equity", "stockholder"],
        }

        # Find which pattern to use based on the requested concepts
        search_patterns = []
        for concept in concept_list:
            if concept in patterns:
                search_patterns.extend(patterns[concept])

        if search_patterns:
            # Look for any concepts matching these patterns
            for concept in facts_data["facts"]["us-gaap"].keys():
                concept_lower = concept.lower()
                if any(pattern in concept_lower for pattern in search_patterns):
                    print(f"Found similar concept: {concept}")
                    # Try to extract data from this concept
                    result = extract_from_facts(facts_data, [concept])
                    if result.get("quarterly_data"):
                        result["original_concept_requested"] = (
                            concept_list[0] if concept_list else "unknown"
                        )
                        return result

    # If we get here, none of the concepts were found
    return {
        "concept": concept_list[0] if concept_list else "unknown",
        "error": "Concept not found in SEC Facts data",
        "quarterly_data": [],
    }


def get_concept_data(cik: str, concept: str) -> Dict[str, Any]:
    """
    Get data for a specific concept from the SEC's API.

    Args:
        cik: Company CIK number
        concept: US GAAP concept name (e.g., "Assets", "Revenue")

    Returns:
        JSON data for the concept across time periods
    """
    # Try different variations of the concept name
    concept_variations = [
        concept,
        concept.lower(),
        concept.upper(),
        "Revenues" if concept == "Revenue" else concept,
        "Revenue" if concept == "Revenues" else concept,
        "NetIncomeLoss" if concept in ["NetIncome", "Income", "Earnings"] else concept,
        "Assets" if concept == "TotalAssets" else concept,
        "Liabilities" if concept == "TotalLiabilities" else concept,
    ]

    # Make the request with each variation until one works
    for concept_var in concept_variations:
        url = COMPANY_CONCEPT_URL.format(cik=cik.zfill(10), concept=concept_var)
        print(f"Trying SEC API with concept: {concept_var}")
        try:
            resp = session.get(url, headers=HEADERS)
            resp.raise_for_status()
            result: Dict[str, Any] = resp.json()
            return result
        except requests.RequestException as e:
            print(f"Error fetching concept {concept_var}: {str(e)}")

    # If we get here, none of the variations worked
    print(f"Could not find data for concept {concept} or its variations")

    # Return an empty structure
    error_dict: Dict[str, Any] = {
        "cik": cik,
        "concept": concept,
        "units": {},
        "error": "Concept not found in SEC data",
    }
    return error_dict


def compare_quarterly_trends(cik: str, concept: str, quarters: int = 4) -> Dict[str, Any]:
    """
    Compare a specific financial concept across multiple quarters.

    Args:
        cik: Company CIK number
        concept: US GAAP concept name (e.g., "Revenue", "NetIncomeLoss")
        quarters: Number of quarters to analyze

    Returns:
        Dictionary with quarterly values and percentage changes
    """
    data = get_concept_data(cik, concept)

    # Extract quarterly data points
    quarterly_data = []

    # Check if data was found
    if "error" in data:
        return {"concept": concept, "error": data["error"], "quarterly_data": []}

    # Get available units
    units = list(data.get("units", {}).keys())[0] if data.get("units") else None

    if units and units in data["units"]:
        facts = data["units"][units]

        # Filter for 10-Q filings
        quarterly_facts = [f for f in facts if f.get("form") == "10-Q"]

        # Sort by end date, most recent first
        quarterly_facts.sort(key=lambda x: x.get("end", ""), reverse=True)

        # Extract the requested number of quarters
        for i, fact in enumerate(quarterly_facts[:quarters]):
            quarterly_data.append(
                {
                    "end_date": fact.get("end"),
                    "value": fact.get("val"),
                    "filing_date": fact.get("filed"),
                }
            )

        # Calculate quarter-over-quarter changes
        for i in range(1, len(quarterly_data)):
            current = quarterly_data[i - 1]["value"]
            previous = quarterly_data[i]["value"]

            if previous and previous != 0:
                pct_change = ((current - previous) / abs(previous)) * 100
                quarterly_data[i - 1]["pct_change_from_previous"] = pct_change

    return {"concept": concept, "quarterly_data": quarterly_data}


def extract_from_html(html_path: str) -> Dict[str, Any]:
    """Extract basic financial data from the HTML filing."""
    print(f"Extracting data from HTML filing: {html_path}")

    with open(html_path, "rb") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find tables in the document
    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables in the document")

    # Financial data to extract
    financial_data: Dict[str, Any] = {
        "revenue": None,
        "net_income": None,
        "total_assets": None,
        "total_liabilities": None,
        "stockholders_equity": None,
    }

    # Keywords to identify relevant tables and rows
    keywords: Dict[str, List[str]] = {
        "revenue": ["revenue", "net sales", "total revenue", "total net revenue"],
        "net_income": ["net income", "net earnings", "net profit", "net loss"],
        "total_assets": ["total assets", "assets total"],
        "total_liabilities": ["total liabilities", "liabilities total"],
        "stockholders_equity": [
            "total stockholders' equity",
            "stockholders' equity",
            "shareholders' equity",
        ],
    }

    # Extract values from tables
    for table_elem in tables:
        # Ensure we're dealing with a Tag object for type safety
        if not isinstance(table_elem, Tag):
            continue

        # Check table headers or caption for financial statement indicators
        table_text = table_elem.get_text().lower()

        if any(
            stmt in table_text
            for stmt in ["income statement", "statement of operations", "statement of income"]
        ):
            print("Found potential income statement")
            parse_table_for_values(table_elem, keywords, financial_data, ["revenue", "net_income"])

        elif any(
            stmt in table_text for stmt in ["balance sheet", "statement of financial position"]
        ):
            print("Found potential balance sheet")
            parse_table_for_values(
                table_elem,
                keywords,
                financial_data,
                ["total_assets", "total_liabilities", "stockholders_equity"],
            )

    return financial_data


def parse_table_for_values(
    table: Tag,
    keywords: Dict[str, List[str]],
    financial_data: Dict[str, Any],
    target_items: List[str],
) -> Dict[str, Any]:
    """Parse a table for specific financial values."""
    rows = table.find_all("tr")

    for row_elem in rows:
        # Ensure we're dealing with a Tag object for type safety
        if not isinstance(row_elem, Tag):
            continue

        # Get all cells in the row
        cells = row_elem.find_all(["td", "th"])
        if not cells or len(cells) < 2:
            continue

        # Get the text of the first cell (usually the label)
        row_label = cells[0].get_text().strip().lower()

        # Check if this row contains data we're looking for
        for item in target_items:
            if financial_data[item] is not None:
                continue  # Already found this item

            # Check if the row label matches any of our keywords for this item
            if any(keyword in row_label for keyword in keywords[item]):
                # Get the value from the last cell (usually the most recent period)
                value_cell = cells[-1].get_text().strip()

                # Try to convert to a number
                try:
                    # Remove currency symbols, commas, and other non-numeric characters
                    value_text = "".join(c for c in value_cell if c.isdigit() or c in ".-")
                    value = float(value_text)
                    financial_data[item] = value
                    print(f"Found {item}: {value}")
                except ValueError:
                    print(f"Could not convert value for {item}: {value_cell}")

    return financial_data


def process_10q_filing(ticker: str, filing_idx: int = 0) -> Dict[str, Any]:
    """
    Process a 10-Q filing and extract financial data using XBRL.

    Args:
        ticker: Stock ticker symbol
        filing_idx: Index of the filing to process (0 = most recent)

    Returns:
        Dictionary with extracted financial data
    """
    try:
        # Get CIK from ticker
        cik = get_cik_from_ticker(ticker)
        print(f"{ticker} → CIK {cik}")

        # Get recent 10-Q filings
        filings = list_recent_filings(cik, form_type="10-Q", count=5)

        if not filings or filing_idx >= len(filings):
            return {"error": f"No 10-Q filing found at index {filing_idx}"}

        filing = filings[filing_idx]
        print(f"Processing 10-Q filed on {filing['date']}...")

        # Try to get data directly from the SEC Facts API first
        print("Trying SEC Facts API...")
        try:
            facts_data = get_facts_from_sec_api(cik)

            # Check if we got useful data
            if facts_data and "facts" in facts_data and isinstance(facts_data["facts"], dict):
                print("Successfully retrieved data from SEC Facts API")

                # Extract ticker from facts
                ticker_from_facts = facts_data.get("entityName", "").split(" ")[0]

                # Process the data to extract quarterly information
                facts_results = {
                    "method": "sec_facts_api",
                    "ticker": ticker_from_facts or ticker,
                    "cik": cik,
                    "filing_date": filing["date"],
                    "accession_number": filing["acc_with_dashes"],
                    "revenue": extract_from_facts(
                        facts_data,
                        ["us-gaap:Revenues", "us-gaap:Revenue", "us-gaap:SalesRevenueNet"],
                    ),
                    "net_income": extract_from_facts(
                        facts_data,
                        ["us-gaap:NetIncomeLoss", "us-gaap:ProfitLoss", "us-gaap:NetIncome"],
                    ),
                    "assets": extract_from_facts(
                        facts_data, ["us-gaap:Assets", "us-gaap:AssetsCurrent"]
                    ),
                    "liabilities": extract_from_facts(
                        facts_data, ["us-gaap:Liabilities", "us-gaap:LiabilitiesCurrent"]
                    ),
                    "stockholders_equity": extract_from_facts(
                        facts_data,
                        [
                            "us-gaap:StockholdersEquity",
                            "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                        ],
                    ),
                }

                # Check if we found any data
                found_data = False
                for key in [
                    "revenue",
                    "net_income",
                    "assets",
                    "liabilities",
                    "stockholders_equity",
                ]:
                    if facts_results[key].get("quarterly_data"):
                        found_data = True
                        break

                if found_data:
                    return facts_results
                else:
                    print("No quarterly data found in Facts API, trying another method...")
            else:
                print("No useful data found in Facts API response")

        except Exception as e:
            print(f"Error with SEC Facts API: {str(e)}, trying XBRL files...")

        # If SEC Facts API didn't work, try the XBRL files
        # Find XBRL files for this filing
        xbrl_files = get_xbrl_files(cik, filing["acc_with_dashes"])

        if not xbrl_files:
            print("No XBRL files found, trying Company Concept API instead...")
            try:
                concept_results = {
                    "method": "sec_concept_api",
                    "filing_date": filing["date"],
                    "revenue": compare_quarterly_trends(cik, "Revenue"),
                    "net_income": compare_quarterly_trends(cik, "NetIncomeLoss"),
                    "assets": compare_quarterly_trends(cik, "Assets"),
                    "liabilities": compare_quarterly_trends(cik, "Liabilities"),
                    "stockholders_equity": compare_quarterly_trends(cik, "StockholdersEquity"),
                }

                # Check if we found any data
                found_data = False
                for key in [
                    "revenue",
                    "net_income",
                    "assets",
                    "liabilities",
                    "stockholders_equity",
                ]:
                    if concept_results[key].get("quarterly_data"):
                        found_data = True
                        break

                if found_data:
                    return concept_results
                else:
                    print("No quarterly data found in Concept API, trying HTML extraction...")
            except Exception as e:
                print(f"Error with Company Concept API: {str(e)}")
        else:
            # Print found files for debugging
            print(f"Found {len(xbrl_files)} XBRL-related files:")
            for i, f in enumerate(xbrl_files):
                print(f"  {i + 1}. {f['name']} (Instance: {f.get('is_instance', False)})")

            # Find the main instance document - prioritize ones marked as instance docs
            instance_docs = [f for f in xbrl_files if f.get("is_instance", False)]

            # If no instance docs found by flag, try to find by filename pattern
            if not instance_docs:
                print("No files marked as instance documents, trying filename patterns...")
                instance_docs = [
                    f
                    for f in xbrl_files
                    if any(pattern in f["name"].lower() for pattern in ["instance", "-", "_"])
                    and not any(
                        suffix in f["name"].lower()
                        for suffix in ["_cal.", "_def.", "_lab.", "_pre."]
                    )
                ]

            # If still no instance docs found, use any .xml or .xbrl file
            if not instance_docs:
                print("No instance documents found by pattern, trying any XML/XBRL file...")
                instance_docs = xbrl_files

            # Try each potential instance document until we find one with facts
            xbrl_results: Dict[str, Any] = {
                "error": "No valid XBRL instance document found with financial facts"
            }

            for doc in instance_docs:
                print(f"Trying file: {doc['name']}")

                # Download and parse the XBRL file
                file_path = download_xbrl_file(doc)
                print(f"Downloaded XBRL file: {file_path}")

                # Parse the XBRL data
                xbrl_data = parse_xbrl_instance(file_path)

                # Check if we got an error
                if "error" in xbrl_data:
                    print(f"Error in file {doc['name']}: {xbrl_data['error']}")
                    continue

                # Check if we have facts
                if not xbrl_data.get("facts"):
                    print(f"No facts found in {doc['name']}")
                    continue

                # Extract financial statements
                financial_data = extract_financial_statements(xbrl_data, filing["date"])

                # If we have some financial data, we're good
                if financial_data and "error" not in financial_data:
                    # Add filing metadata
                    xbrl_results = {
                        "method": "xbrl_file",
                        "ticker": ticker,
                        "cik": cik,
                        "filing_date": filing["date"],
                        "accession_number": filing["acc_with_dashes"],
                        "financial_data": financial_data,
                        "source_file": doc["name"],
                    }
                    break

            if "error" not in xbrl_results:
                return xbrl_results
            else:
                print("Could not extract data from XBRL files, trying HTML extraction...")

        # If all else fails, try HTML extraction
        print("Trying HTML filing extraction as last resort...")
        try:
            # Download the HTML filing
            html_path = download_html_filing(cik, filing["acc_with_dashes"], filing["doc"])

            # Extract data from the HTML
            html_data = extract_from_html(html_path)

            # Check if we found any useful data
            if any(value is not None for value in html_data.values()):
                return {
                    "method": "html_extraction",
                    "ticker": ticker,
                    "cik": cik,
                    "filing_date": filing["date"],
                    "accession_number": filing["acc_with_dashes"],
                    "financial_data": html_data,
                    "source_file": html_path,
                }
            else:
                return {"error": "Could not extract financial data using any method"}
        except Exception as e:
            print(f"Error with HTML extraction: {str(e)}")
            return {"error": f"Failed to extract data: {str(e)}"}

    except Exception as e:
        print(f"Error processing filing: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def save_results_to_json(data: Dict[str, Any], output_file: str = "10q_data.json"):
    """Save extracted data to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {output_file}")


def display_financial_summary(results: Dict[str, Any]):
    """Print a summary of the extracted financial data."""
    if "error" in results:
        print(f"Error: {results['error']}")
        return

    print(f"\nData Source: {results['method']}")

    if results["method"] == "xbrl_file":
        financial_data = results.get("financial_data", {})
        print(f"Quarter End Date: {financial_data.get('quarter_end_date')}")

        print("\nBalance Sheet Highlights:")
        for key, value in financial_data.get("balance_sheet", {}).items():
            print(f"  {key}: {value.get('value'):,.2f} {value.get('unit')}")

        print("\nIncome Statement Highlights:")
        for key, value in financial_data.get("income_statement", {}).items():
            print(f"  {key}: {value.get('value'):,.2f} {value.get('unit')}")

        print("\nCash Flow Highlights:")
        for key, value in financial_data.get("cash_flow", {}).items():
            print(f"  {key}: {value.get('value'):,.2f} {value.get('unit')}")

    elif results["method"] in ["sec_facts_api", "sec_concept_api"]:
        # Display revenue data
        if "revenue" in results and results["revenue"].get("quarterly_data"):
            print("\nQuarterly Revenue Trend:")
            for quarter in results["revenue"]["quarterly_data"]:
                change = quarter.get("pct_change_from_previous")
                change_str = f" ({change:.2f}% from previous)" if change is not None else ""
                print(f"  {quarter.get('end_date')}: {quarter.get('value'):,.2f}{change_str}")

        # Display net income data
        if "net_income" in results and results["net_income"].get("quarterly_data"):
            print("\nQuarterly Net Income Trend:")
            for quarter in results["net_income"]["quarterly_data"]:
                change = quarter.get("pct_change_from_previous")
                change_str = f" ({change:.2f}% from previous)" if change is not None else ""
                print(f"  {quarter.get('end_date')}: {quarter.get('value'):,.2f}{change_str}")

        # Display assets data if available
        if "assets" in results and results["assets"].get("quarterly_data"):
            print("\nTotal Assets:")
            for quarter in results["assets"]["quarterly_data"]:
                print(f"  {quarter.get('end_date')}: {quarter.get('value'):,.2f}")

        # Display liabilities data if available
        if "liabilities" in results and results["liabilities"].get("quarterly_data"):
            print("\nTotal Liabilities:")
            for quarter in results["liabilities"]["quarterly_data"]:
                print(f"  {quarter.get('end_date')}: {quarter.get('value'):,.2f}")

        # Display stockholders' equity data if available
        if "stockholders_equity" in results and results["stockholders_equity"].get(
            "quarterly_data"
        ):
            print("\nStockholders' Equity:")
            for quarter in results["stockholders_equity"]["quarterly_data"]:
                print(f"  {quarter.get('end_date')}: {quarter.get('value'):,.2f}")

    elif results["method"] == "html_extraction":
        print("\nExtracted from HTML filing:")
        financial_data = results.get("financial_data", {})

        if financial_data.get("revenue") is not None:
            print(f"  Revenue: {financial_data['revenue']:,.2f}")
        if financial_data.get("net_income") is not None:
            print(f"  Net Income: {financial_data['net_income']:,.2f}")
        if financial_data.get("total_assets") is not None:
            print(f"  Total Assets: {financial_data['total_assets']:,.2f}")
        if financial_data.get("total_liabilities") is not None:
            print(f"  Total Liabilities: {financial_data['total_liabilities']:,.2f}")
        if financial_data.get("stockholders_equity") is not None:
            print(f"  Stockholders' Equity: {financial_data['stockholders_equity']:,.2f}")

    else:
        print("Unknown data format")


if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"  # Change to any ticker you want

    # Process the most recent 10-Q
    results = process_10q_filing(ticker)

    # Save results to JSON
    save_results_to_json(results, f"{ticker}_10q_data.json")

    # Display a summary of the extracted data
    display_financial_summary(results)

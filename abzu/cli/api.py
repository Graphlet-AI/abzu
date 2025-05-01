"""API access module for Abzu."""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FinancialDatasetsAPI:
    """Client for the Financial Datasets API."""

    BASE_URL = "https://api.financialdatasets.ai"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the API client.

        Args:
            api_key: API key for Financial Datasets. If None, will attempt to read from
                     FINANCIAL_DATASETS_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set the FINANCIAL_DATASETS_API_KEY environment variable or "
                "pass an api_key parameter."
            )

        self.headers = {"X-API-KEY": self.api_key}

    def get_company_facts(
        self, ticker: Optional[str] = None, cik: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get company facts from the Financial Datasets API.

        Args:
            ticker: Company ticker symbol (optional if cik is provided)
            cik: Central Index Key (optional if ticker is provided)

        Returns:
            Dictionary containing company facts

        Raises:
            ValueError: If neither ticker nor cik is provided
            requests.RequestException: If the API request fails
        """
        if not ticker and not cik:
            raise ValueError("Either ticker or cik parameter is required")

        params = {}
        if ticker:
            params["ticker"] = ticker
        if cik:
            params["cik"] = cik

        url = f"{self.BASE_URL}/company/facts"

        try:
            response: requests.Response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            logger.error(f"Response: {response.text}")
            raise


def read_jsonl(file_path: str) -> Iterator[Dict[str, Any]]:
    """Read a JSON Lines file and yield each line as a parsed JSON object.

    Args:
        file_path: Path to the JSON Lines file

    Yields:
        Each line parsed as a JSON object
    """
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping invalid JSON line: {line}")


def process_batch_companies(
    api: FinancialDatasetsAPI,
    companies: List[Dict[str, Any | None]],
    output_file: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Process a batch of companies in parallel.

    Args:
        api: FinancialDatasetsAPI instance
        companies: List of dictionaries with ticker and/or cik keys
        output_file: File to write results to (if None, return without writing)

    Returns:
        List of API results
    """
    results = []

    def process_company(company: Dict[str, str]) -> Dict[str, Any | None]:
        """Process a single company."""
        ticker = company.get("ticker")
        cik = company.get("cik")
        if not ticker and not cik:
            logger.warning(f"Skipping record missing both ticker and cik: {company}")
            return {}

        try:
            result = api.get_company_facts(ticker, cik)
            # Include the original request parameters in the result
            result["request"] = {"ticker": ticker, "cik": cik}
            return result
        except Exception as e:
            logger.error(f"Error retrieving company facts for {ticker or cik}: {e}")
            return {"error": str(e), "request": {"ticker": ticker, "cik": cik}}

    # Process companies in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_company, companies))

    # Write results if output file is specified
    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, "w") as f:
            for result in results:
                if result:  # Skip empty results
                    f.write(json.dumps(result) + "\n")
        logger.info(f"Results written to {output_file}")

    return results


def financialdatasets_facts_main(  # noqa: C901
    ticker: Optional[str] = None,
    cik: Optional[str] = None,
    input_file: Optional[str] = None,
    api_key: Optional[str] = None,
    pretty: bool = False,
    output_file: Optional[str] = None,
) -> int:
    """Get company facts from the Financial Datasets API.

    Args:
        ticker: Company ticker symbol
        cik: Central Index Key
        input_file: Path to a JSONL file with records containing 'ticker' or 'cik' field
        api_key: API key for Financial Datasets
        pretty: Whether to format JSON output with indentation (only used for stdout output)
        output_file: File to write results to (if None, print to stdout)

    Returns:
        0 on success, 1 on failure
    """
    try:
        # The validation is now handled by the click command

        api = FinancialDatasetsAPI(api_key)

        # Case 1: Process a single company using ticker/cik
        if not input_file:
            result = api.get_company_facts(ticker, cik)

            # Write or print the result
            if output_file:
                os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(json.dumps(result) + "\n")
                logger.info(f"Results written to {output_file}")
            else:
                # Pretty format only when printing to stdout (not file)
                if pretty:
                    print(json.dumps(result, indent=2))
                else:
                    print(json.dumps(result))

        # Case 2: Process companies from an input file
        else:
            if not os.path.exists(input_file):
                logger.error(f"Input file does not exist: {input_file}")
                return 1

            # Read companies from JSONL file
            companies: List[Dict[str, Any | None]] = []
            for record in read_jsonl(input_file):
                ticker_val = record.get("ticker")
                cik_val = record.get("cik")
                if ticker_val or cik_val:
                    companies.append({"ticker": ticker_val, "cik": cik_val})

            if not companies:
                logger.error(f"No valid records with 'ticker' or 'cik' found in {input_file}")
                return 1

            logger.info(f"Processing {len(companies)} companies from {input_file}")
            process_batch_companies(api, companies, output_file)

        return 0
    except Exception as e:
        logger.error(f"Error retrieving company facts: {e}")
        return 1


def main() -> int:
    """Command line interface for API module."""
    return financialdatasets_facts_main()


if __name__ == "__main__":
    import sys

    sys.exit(main())

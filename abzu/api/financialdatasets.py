"""Financial Datasets API client for Abzu."""

import json
import logging
import os
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FinancialDatasetsAPI:
    """Client for the Financial Datasets API."""

    BASE_URL = "https://api.financialdatasets.ai"

    def __init__(
        self, api_key: Optional[str] = None, max_retries: int = 5, pause_seconds: float = 0.5
    ):
        """Initialize the API client with retry capabilities.

        Args:
            api_key: API key for Financial Datasets. If None, will attempt to read from
                     FINANCIAL_DATASETS_API_KEY environment variable.
            max_retries: Maximum number of retries for rate-limited requests (429 status code).
                         Defaults to 5.
            pause_seconds: Number of seconds to pause between API requests to prevent rate limiting.
                           Defaults to 0.5 seconds.
        """
        self.api_key = api_key or os.environ.get("FINANCIAL_DATASETS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set the FINANCIAL_DATASETS_API_KEY environment variable or "
                "pass an api_key parameter."
            )

        self.headers = {"X-API-KEY": self.api_key}
        self.pause_seconds = pause_seconds

        # Configure session with retry capabilities
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429],  # Only retry on 429 Too Many Requests
            allowed_methods=["GET"],  # Only retry GET requests
            backoff_factor=1,  # Exponential backoff: 1, 2, 4, 8, 16 seconds
            respect_retry_after_header=True,  # Honor Retry-After header
            raise_on_status=True,  # Raise exception on status codes in status_forcelist
        )

        # Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_company_facts(
        self, ticker: Optional[str] = None, cik: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get company facts from the Financial Datasets API with rate limiting.

        This method uses exponential backoff retry for rate-limited requests (HTTP 429 status code).
        It will retry up to the configured maximum number of retries before failing.

        Args:
            ticker: Company ticker symbol (optional if cik is provided)
            cik: Central Index Key (optional if ticker is provided)

        Returns:
            Dictionary containing company facts

        Raises:
            ValueError: If neither ticker nor cik is provided
            requests.RequestException: If the API request fails after all retries
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
            # Add a pause before making the request to prevent rate limiting
            if self.pause_seconds > 0:
                logger.debug(f"Pausing for {self.pause_seconds} seconds before API request")
                time.sleep(self.pause_seconds)

            # Use session with retry configuration instead of direct requests.get
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.exceptions.RetryError as e:
            logger.error(f"API request failed after multiple retries: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
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


def read_parquet(file_path: str) -> Iterator[Dict[str, Any]]:
    """Read a Parquet file and yield each row as a dictionary.

    Args:
        file_path: Path to the Parquet file

    Yields:
        Each row as a dictionary

    Raises:
        ImportError: If pyarrow or pandas is not installed
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error(
            "pandas package is required to read Parquet files. Install with: pip install pandas pyarrow"
        )
        raise

    try:
        # Read the parquet file into a pandas DataFrame
        df = pd.read_parquet(file_path)

        # Convert DataFrame to dictionaries
        for record in df.to_dict(orient="records"):
            yield {str(k): v for k, v in record.items()}
    except Exception as e:
        logger.error(f"Error reading Parquet file: {e}")
        raise


def read_data_file(file_path: str) -> Iterator[Dict[str, Any]]:
    """Read a data file (JSONL or Parquet) based on file extension.

    Args:
        file_path: Path to the data file

    Yields:
        Each record as a dictionary

    Raises:
        ValueError: If file format is not supported
    """
    file_ext = pathlib.Path(file_path).suffix.lower()

    if file_ext in (".jsonl", ".json"):
        yield from read_jsonl(file_path)
    elif file_ext == ".parquet":
        yield from read_parquet(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {file_ext}. Supported formats: .jsonl, .json, .parquet"
        )


def process_batch_companies(
    api: FinancialDatasetsAPI,
    companies: List[Dict[str, Any | None]],
    output_file: Optional[str] = None,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Process a batch of companies in parallel.

    Args:
        api: FinancialDatasetsAPI instance
        companies: List of dictionaries with ticker and/or cik keys
        output_file: File to write results to (if None, return without writing)
        show_progress: Whether to display a progress bar (default: True)

    Returns:
        List of API results
    """
    results = []
    total_companies = len(companies)
    logger.info(f"Processing {total_companies} companies")

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
        # Use tqdm to show progress
        if show_progress:
            results = list(
                tqdm(
                    executor.map(process_company, companies),
                    total=total_companies,
                    desc="Processing companies",
                    unit="company",
                )
            )
        else:
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
    max_retries: int = 5,
    pause_seconds: float = 0.5,
    show_progress: bool = True,
) -> int:
    """Get company facts from the Financial Datasets API.

    Args:
        ticker: Company ticker symbol
        cik: Central Index Key
        input_file: Path to a file (JSONL or Parquet) with records containing 'ticker', 'symbol', or 'cik' field
        api_key: API key for Financial Datasets
        pretty: Whether to format JSON output with indentation (only used for stdout output)
        output_file: File to write results to (only used when processing multiple companies, default: data/financialdatasets.jsonl)
        max_retries: Maximum number of retries for rate-limited requests (429 status code). Defaults to 5.
        pause_seconds: Number of seconds to pause between API requests to prevent rate limiting. Defaults to 0.5.
        show_progress: Whether to display a progress bar when processing multiple companies. Defaults to True.

    Returns:
        0 on success, 1 on failure
    """
    try:
        # The validation is now handled by the click command

        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=pause_seconds)

        # Case 1: Process a single company using ticker/cik
        if not input_file:
            result = api.get_company_facts(ticker, cik)

            # Write or print the result
            if output_file is not None:
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

        # Case 2: Process companies from an input file (JSONL or Parquet)
        else:
            if not os.path.exists(input_file):
                logger.error(f"Input file does not exist: {input_file}")
                return 1

            # Detect file format and read records accordingly
            try:
                # Read companies from data file
                companies: List[Dict[str, Any | None]] = []
                for record in read_data_file(input_file):
                    # Check for ticker/symbol and cik fields
                    ticker_val = record.get("ticker") or record.get("symbol")
                    cik_val = record.get("cik")
                    if ticker_val or cik_val:
                        companies.append({"ticker": ticker_val, "cik": cik_val})

                if not companies:
                    logger.error(
                        f"No valid records with 'ticker', 'symbol', or 'cik' found in {input_file}"
                    )
                    return 1

                logger.info(f"Processing {len(companies)} companies from {input_file}")
                process_batch_companies(api, companies, output_file, show_progress=show_progress)

            except ValueError as e:
                logger.error(f"Error reading input file: {e}")
                return 1

        return 0
    except Exception as e:
        logger.error(f"Error retrieving company facts: {e}")
        return 1

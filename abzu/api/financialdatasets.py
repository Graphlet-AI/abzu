"""Financial Datasets API client for Abzu."""

import json
import os
import pathlib
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Any, Iterator, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

from abzu.config import config
from abzu.logs import get_logger

logger = get_logger(__name__)


class FinancialDatasetsAPI:
    """Client for the Financial Datasets API."""

    BASE_URL = "https://api.financialdatasets.ai"

    def __init__(
        self, api_key: Optional[str] = None, max_retries: int = 5, pause_seconds: float = 0.6
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

    def get_historical_prices(
        self,
        ticker: str,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        interval: str = "day",
        interval_multiplier: int = 1,
    ) -> dict[str, Any]:
        """Get historical price data for a ticker.

        This method retrieves historical price data for a specific ticker symbol at the
        specified time interval within the required start and end date range.

        Args:
            ticker: The ticker symbol (e.g., 'AAPL' for Apple)
            start_date: The start date for the price data. Can be a string in YYYY-MM-DD format,
                       a datetime object, or a date object.
            end_date: The end date for the price data. Can be a string in YYYY-MM-DD format,
                     a datetime object, or a date object.
            interval: The time interval for the price data. Possible values are
                     'second', 'minute', 'day', 'week', 'month', 'year'.
                     Defaults to 'day'.
            interval_multiplier: The multiplier for the interval (e.g., 5 for every 5 minutes).
                                 Defaults to 1.

        Returns:
            Dictionary containing historical price data with 'prices' key

        Raises:
            ValueError: If ticker is not provided or interval is invalid
            requests.RequestException: If the API request fails after all retries
        """
        if not ticker:
            raise ValueError("Ticker parameter is required")

        if not start_date:
            raise ValueError("Start date parameter is required")

        if not end_date:
            raise ValueError("End date parameter is required")

        valid_intervals = {"second", "minute", "day", "week", "month", "year"}
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}. Must be one of {valid_intervals}")

        # Format and validate dates
        if isinstance(start_date, (date, datetime)):
            formatted_start_date = start_date.strftime("%Y-%m-%d")
        else:
            # Validate ISO date format (YYYY-MM-DD)
            if not isinstance(start_date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", start_date):
                raise ValueError(
                    "Start date must be in ISO format (YYYY-MM-DD), a date object, or a datetime object"
                )
            formatted_start_date = start_date

        if isinstance(end_date, (date, datetime)):
            formatted_end_date = end_date.strftime("%Y-%m-%d")
        else:
            # Validate ISO date format (YYYY-MM-DD)
            if not isinstance(end_date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", end_date):
                raise ValueError(
                    "End date must be in ISO format (YYYY-MM-DD), a date object, or a datetime object"
                )
            formatted_end_date = end_date

        # Create parameter dictionary with explicit string values for type compatibility
        params = {
            "ticker": str(ticker),
            "interval": str(interval),
            "interval_multiplier": str(interval_multiplier),
            "start_date": str(formatted_start_date),
            "end_date": str(formatted_end_date),
        }

        url = f"{self.BASE_URL}/prices/"

        try:
            # Add a pause before making the request to prevent rate limiting
            if self.pause_seconds > 0:
                logger.debug(f"Pausing for {self.pause_seconds} seconds before API request")
                time.sleep(self.pause_seconds)

            # Use session with retry configuration
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.exceptions.RetryError as e:
            logger.error(f"API request for prices failed after multiple retries: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"API request for prices failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_company_facts(
        self, ticker: Optional[str] = None, cik: Optional[str] = None
    ) -> dict[str, Any]:
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

    def get_tickers(self) -> dict[str, Any]:
        """Get all available tickers from the Financial Datasets API.

        This method retrieves a list of all available ticker symbols and their associated
        company information from the Financial Datasets API.

        Returns:
            Dictionary containing ticker symbols and company information

        Raises:
            requests.exceptions.RetryError: If the API request fails after multiple retries
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}/company/facts/tickers"

        try:
            # Use session with retry configuration
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.exceptions.RetryError as e:
            logger.error(f"API request for tickers failed after multiple retries: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"API request for tickers failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_multiple_prices(
        self,
        tickers: list[str],
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        interval: str = "day",
        interval_multiplier: int = 1,
        max_workers: int = 5,
        show_progress: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Get historical price data for multiple tickers in parallel.

        This method retrieves historical price data for multiple ticker symbols at the
        specified time interval within the required start and end date range.
        Requests are executed in parallel using ThreadPoolExecutor.

        Args:
            tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOG'])
            start_date: The start date for the price data. Can be a string in YYYY-MM-DD format,
                      a datetime object, or a date object.
            end_date: The end date for the price data. Can be a string in YYYY-MM-DD format,
                     a datetime object, or a date object.
            interval: The time interval for the price data. Possible values are
                     'second', 'minute', 'day', 'week', 'month', 'year'.
                     Defaults to 'day'.
            interval_multiplier: The multiplier for the interval (e.g., 5 for every 5 minutes).
                                Defaults to 1.
            max_workers: Maximum number of parallel workers for API requests. Defaults to 5.
            show_progress: Whether to display a progress bar. Defaults to True.

        Returns:
            Dictionary mapping ticker symbols to their respective price data

        Raises:
            ValueError: If tickers list is empty, or interval is invalid
        """
        if not tickers:
            raise ValueError("Tickers list cannot be empty")

        # Format dates once for all requests
        if isinstance(start_date, (date, datetime)):
            formatted_start_date = start_date.strftime("%Y-%m-%d")
        else:
            # Validate ISO date format (YYYY-MM-DD)
            if not isinstance(start_date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", start_date):
                raise ValueError(
                    "Start date must be in ISO format (YYYY-MM-DD), a date object, or a datetime object"
                )
            formatted_start_date = start_date

        if isinstance(end_date, (date, datetime)):
            formatted_end_date = end_date.strftime("%Y-%m-%d")
        else:
            # Validate ISO date format (YYYY-MM-DD)
            if not isinstance(end_date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", end_date):
                raise ValueError(
                    "End date must be in ISO format (YYYY-MM-DD), a date object, or a datetime object"
                )
            formatted_end_date = end_date

        valid_intervals = {"second", "minute", "day", "week", "month", "year"}
        if interval not in valid_intervals:
            raise ValueError(f"Invalid interval: {interval}. Must be one of {valid_intervals}")

        # Function to get price data for a single ticker
        def get_ticker_prices(ticker: str) -> tuple[str, dict[str, Any]]:
            try:
                result = self.get_historical_prices(
                    ticker=ticker,
                    start_date=formatted_start_date,
                    end_date=formatted_end_date,
                    interval=interval,
                    interval_multiplier=interval_multiplier,
                )
                return ticker, result
            except Exception as e:
                logger.error(f"Error retrieving price data for {ticker}: {e}")
                return ticker, {"error": str(e)}

        results: dict[str, dict[str, Any]] = {}

        # Process tickers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(get_ticker_prices, ticker): ticker for ticker in tickers}

            # Use tqdm to show progress if requested
            if show_progress:
                completed_futures = tqdm(
                    futures, total=len(futures), desc="Retrieving price data", unit="ticker"
                )
            else:
                completed_futures = futures

            for future in completed_futures:
                try:
                    ticker, result = future.result()
                    results[ticker] = result
                except Exception as e:
                    # This exception is from the future itself, not the API call
                    ticker = futures[future]
                    logger.error(f"Unhandled exception for ticker {ticker}: {e}")
                    results[ticker] = {"error": str(e)}

        return results

    def get_financial_metrics(
        self, ticker: str, period: str = "annual", limit: int = 30
    ) -> dict[str, Any]:
        """Get financial metrics for a ticker from the Financial Datasets API.

        This method retrieves financial metrics for a specific ticker symbol with
        the specified period and limit.

        Args:
            ticker: The ticker symbol (e.g., 'AAPL' for Apple)
            period: The period for financial metrics. Possible values are
                   'annual', 'quarterly', or 'ttm' (trailing twelve months).
                   Defaults to 'annual'.
            limit: Number of periods to return. Defaults to 30.

        Returns:
            Dictionary containing financial metrics

        Raises:
            ValueError: If ticker is not provided or period is invalid
            requests.RequestException: If the API request fails after all retries
        """
        if not ticker:
            raise ValueError("Ticker parameter is required")

        valid_periods = {"annual", "quarterly", "ttm"}
        if period not in valid_periods:
            raise ValueError(f"Invalid period: {period}. Must be one of {valid_periods}")

        # Create parameter dictionary with explicit string values for type compatibility
        params = {"ticker": str(ticker), "period": str(period), "limit": str(limit)}

        url = f"{self.BASE_URL}/financial-metrics"

        try:
            # Add a pause before making the request to prevent rate limiting
            if self.pause_seconds > 0:
                logger.debug(f"Pausing for {self.pause_seconds} seconds before API request")
                time.sleep(self.pause_seconds)

            # Use session with retry configuration
            response = self.session.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()  # type: ignore
        except requests.exceptions.RetryError as e:
            logger.error(f"API request for financial metrics failed after multiple retries: {e}")
            raise
        except requests.RequestException as e:
            logger.error(f"API request for financial metrics failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise


def read_jsonl(file_path: str) -> Iterator[dict[str, Any]]:
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


def read_parquet(file_path: str) -> Iterator[dict[str, Any]]:
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


def read_data_file(file_path: str) -> Iterator[dict[str, Any]]:
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
    companies: list[dict[str, Any | None]],
    output_file: Optional[str] = None,
    show_progress: bool = True,
) -> list[dict[str, Any]]:
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

    def process_company(company: dict[str, str]) -> dict[str, Any | None]:
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
        output_file: File to write results to (only used when processing multiple companies).
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
                companies: list[dict[str, Any | None]] = []
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


def financialdatasets_price_main(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "day",
    interval_multiplier: int = 1,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    pretty: bool = False,
    max_retries: int = 5,
    pause_seconds: float = 0.5,
) -> int:
    """Get historical price data for a ticker from the Financial Datasets API.

    This function retrieves historical price data for a specific ticker symbol
    at the specified time interval within a date range and saves it to a file or prints it to stdout.

    Args:
        ticker: The ticker symbol (e.g., 'AAPL' for Apple)
        start_date: The start date for the price data in ISO format (YYYY-MM-DD)
        end_date: The end date for the price data in ISO format (YYYY-MM-DD)
        interval: The time interval for the price data. Possible values are
                 'second', 'minute', 'day', 'week', 'month', 'year'.
                 Defaults to 'day'.
        interval_multiplier: The multiplier for the interval (e.g., 5 for every 5 minutes).
                             Defaults to 1.
        api_key: API key for Financial Datasets. If None, will attempt to read from
                 FINANCIAL_DATASETS_API_KEY environment variable.
        output_file: File to write results to. If None, results are printed to stdout.
        pretty: Whether to format JSON output with indentation
        max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.
        pause_seconds: Number of seconds to pause between API requests. Defaults to 0.5.

    Returns:
        0 on success, 1 on failure
    """
    try:
        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=pause_seconds)

        # Get historical price data
        logger.info(f"Retrieving price data for {ticker} from {start_date} to {end_date}")
        result = api.get_historical_prices(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            interval_multiplier=interval_multiplier,
        )

        # Write or print the result
        if output_file:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            logger.info(f"Writing price data to {output_file}")
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(result, f, indent=2)
                else:
                    json.dump(result, f)
            logger.info(f"Successfully wrote price data to {output_file}")
        else:
            # Print to stdout with or without indentation
            if pretty:
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(result))

        return 0
    except Exception as e:
        logger.error(f"Error retrieving price data: {e}")
        return 1


def financialdatasets_metrics_main(
    ticker: str,
    period: str = "annual",
    limit: int = 30,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    pretty: bool = False,
    max_retries: int = 5,
    pause_seconds: float = 0.5,
) -> int:
    """Get financial metrics for a ticker from the Financial Datasets API.

    This function retrieves financial metrics for a specific ticker symbol with
    the specified period and limit, and saves it to a file or prints it to stdout.

    Args:
        ticker: The ticker symbol (e.g., 'AAPL' for Apple)
        period: The period for financial metrics. Possible values are
                'annual', 'quarterly', or 'ttm' (trailing twelve months).
                Defaults to 'annual'.
        limit: Number of periods to return. Defaults to 30.
        api_key: API key for Financial Datasets. If None, will attempt to read from
                FINANCIAL_DATASETS_API_KEY environment variable.
        output_file: File to write results to. If None, results are printed to stdout.
        pretty: Whether to format JSON output with indentation
        max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.
        pause_seconds: Number of seconds to pause between API requests. Defaults to 0.5.

    Returns:
        0 on success, 1 on failure
    """
    try:
        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=pause_seconds)

        # Get financial metrics
        logger.info(
            f"Retrieving financial metrics for {ticker} with period={period}, limit={limit}"
        )
        result = api.get_financial_metrics(
            ticker=ticker,
            period=period,
            limit=limit,
        )

        # Write or print the result
        if output_file:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            logger.info(f"Writing financial metrics to {output_file}")
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(result, f, indent=2)
                else:
                    json.dump(result, f)
            logger.info(f"Successfully wrote financial metrics to {output_file}")
        else:
            # Print to stdout with or without indentation
            if pretty:
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(result))

        return 0
    except Exception as e:
        logger.error(f"Error retrieving financial metrics: {e}")
        return 1


def financialdatasets_metrics_multiple_main(
    tickers: list[str],
    period: str = "annual",
    limit: int = 30,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    pretty: bool = False,
    max_retries: int = 5,
    pause_seconds: float = 0.5,
    max_workers: int = 5,
    show_progress: bool = True,
) -> int:
    """Get financial metrics for multiple tickers from the Financial Datasets API.

    This function retrieves financial metrics for multiple ticker symbols with
    the specified period and limit, and saves the combined results to a file.
    Requests are executed in parallel for better performance.

    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOG'])
        period: The period for financial metrics. Possible values are
               'annual', 'quarterly', or 'ttm' (trailing twelve months).
               Defaults to 'annual'.
        limit: Number of periods to return. Defaults to 30.
        api_key: API key for Financial Datasets. If None, will attempt to read from
                FINANCIAL_DATASETS_API_KEY environment variable.
        output_file: File to write results to. If None, results are printed to stdout.
        pretty: Whether to format JSON output with indentation
        max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.
        pause_seconds: Number of seconds to pause between API requests. Defaults to 0.5.
        max_workers: Maximum number of parallel workers for API requests. Defaults to 5.
        show_progress: Whether to display a progress bar. Defaults to True.

    Returns:
        0 on success, 1 on failure
    """
    try:
        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=pause_seconds)

        # Get metrics for all tickers
        ticker_count = len(tickers)
        logger.info(
            f"Retrieving financial metrics for {ticker_count} tickers with period={period}, limit={limit}"
        )

        # Function to get metrics for a single ticker
        def get_ticker_metrics(ticker: str) -> tuple[str, dict[str, Any]]:
            try:
                result = api.get_financial_metrics(
                    ticker=ticker,
                    period=period,
                    limit=limit,
                )
                return ticker, result
            except Exception as e:
                logger.error(f"Error retrieving metrics for {ticker}: {e}")
                return ticker, {"error": str(e)}

        results: dict[str, dict[str, Any]] = {}

        # Process tickers in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(get_ticker_metrics, ticker): ticker for ticker in tickers}

            # Use tqdm to show progress if requested
            if show_progress:
                completed_futures = tqdm(
                    futures, total=len(futures), desc="Retrieving financial metrics", unit="ticker"
                )
            else:
                completed_futures = futures

            for future in completed_futures:
                try:
                    ticker, result = future.result()
                    results[ticker] = result
                except Exception as e:
                    # This exception is from the future itself, not the API call
                    ticker = futures[future]
                    logger.error(f"Unhandled exception for ticker {ticker}: {e}")
                    results[ticker] = {"error": str(e)}

        # Write or print the result
        if output_file:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            logger.info(f"Writing financial metrics for {ticker_count} tickers to {output_file}")
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(results, f, indent=2)
                else:
                    json.dump(results, f)
            logger.info(f"Successfully wrote financial metrics to {output_file}")
        else:
            # Print to stdout with or without indentation
            if pretty:
                print(json.dumps(results, indent=2))
            else:
                print(json.dumps(results))

        return 0
    except Exception as e:
        logger.error(f"Error retrieving financial metrics for multiple tickers: {e}")
        return 1


def financialdatasets_price_multiple_main(
    tickers: list[str],
    start_date: str,
    end_date: str,
    interval: str = "day",
    interval_multiplier: int = 1,
    api_key: Optional[str] = None,
    output_file: Optional[str] = None,
    pretty: bool = False,
    max_retries: int = 5,
    pause_seconds: float = 0.5,
    max_workers: int = 5,
    show_progress: bool = True,
) -> int:
    """Get historical price data for multiple tickers from the Financial Datasets API.

    This function retrieves historical price data for multiple ticker symbols at the
    specified time interval within a date range and saves it to a file or prints it to stdout.
    Requests are executed in parallel for better performance.

    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOG'])
        start_date: The start date for the price data in ISO format (YYYY-MM-DD)
        end_date: The end date for the price data in ISO format (YYYY-MM-DD)
        interval: The time interval for the price data. Possible values are
                 'second', 'minute', 'day', 'week', 'month', 'year'.
                 Defaults to 'day'.
        interval_multiplier: The multiplier for the interval (e.g., 5 for every 5 minutes).
                             Defaults to 1.
        api_key: API key for Financial Datasets. If None, will attempt to read from
                 FINANCIAL_DATASETS_API_KEY environment variable.
        output_file: File to write results to. If None, results are printed to stdout.
        pretty: Whether to format JSON output with indentation
        max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.
        pause_seconds: Number of seconds to pause between API requests. Defaults to 0.5.
        max_workers: Maximum number of parallel workers for API requests. Defaults to 5.
        show_progress: Whether to display a progress bar. Defaults to True.

    Returns:
        0 on success, 1 on failure
    """
    try:
        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=pause_seconds)

        # Get historical price data for all tickers
        ticker_count = len(tickers)
        logger.info(
            f"Retrieving price data for {ticker_count} tickers from {start_date} to {end_date}"
        )

        # Execute parallel API requests for all tickers
        result = api.get_multiple_prices(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            interval_multiplier=interval_multiplier,
            max_workers=max_workers,
            show_progress=show_progress,
        )

        # Write or print the result
        if output_file:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            logger.info(f"Writing price data for {ticker_count} tickers to {output_file}")
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(result, f, indent=2)
                else:
                    json.dump(result, f)
            logger.info(f"Successfully wrote price data to {output_file}")
        else:
            # Print to stdout with or without indentation
            if pretty:
                print(json.dumps(result, indent=2))
            else:
                print(json.dumps(result))

        return 0
    except Exception as e:
        logger.error(f"Error retrieving price data for multiple tickers: {e}")
        return 1


def financialdatasets_tickers_main(
    api_key: Optional[str] = None,
    output_file: str = config.get("api.financialdatasets.tickers.output"),
    pretty: bool = False,
    max_retries: int = 5,
) -> int:
    """Get all available tickers from the Financial Datasets API.

    This function retrieves all ticker symbols from the Financial Datasets API
    and stores them in a JSON file.

    Args:
        api_key: API key for Financial Datasets
        output_file: Path to the output file (default: data/financialdatasets/tickers.json)
        pretty: Whether to format JSON output with indentation
        max_retries: Maximum number of retries for rate-limited requests. Defaults to 5.

    Returns:
        0 on success, 1 on failure
    """
    try:
        api = FinancialDatasetsAPI(api_key, max_retries=max_retries, pause_seconds=0)

        # Get all tickers from the API
        logger.info("Retrieving all tickers from Financial Datasets API")
        result = api.get_tickers()

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        # Write the result to the output file
        logger.info(f"Writing tickers to {output_file}")
        with open(output_file, "w") as f:
            if pretty:
                json.dump(result, f, indent=2)
            else:
                json.dump(result, f)

        logger.info(f"Successfully wrote tickers data to {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Error retrieving tickers: {e}")
        return 1

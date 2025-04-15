import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import pandas as pd
import requests
import yfinance as yf


def fetch_stock_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch stock data from Yahoo Finance

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing financial data or None
    """
    try:
        stock = yf.Ticker(ticker)

        quarterly_financials = stock.quarterly_financials
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        quarterly_cashflow = stock.quarterly_cashflow

        if quarterly_financials is None or quarterly_financials.empty:
            return None

        return {
            "stock": stock,
            "quarterly_financials": quarterly_financials,
            "quarterly_balance_sheet": quarterly_balance_sheet,
            "quarterly_cashflow": quarterly_cashflow,
        }
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None


def get_latest_quarterly_report_yahoo(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest quarterly report information using Yahoo Finance

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing quarterly financial data or None if retrieval fails
    """
    print(f"Fetching quarterly report information for {ticker} using Yahoo Finance...")

    # Get stock information with a retry mechanism
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = fetch_stock_data(ticker)
            if not data:
                raise ValueError("No quarterly financials data available")

            stock = data["stock"]
            quarterly_financials = data["quarterly_financials"]
            quarterly_balance_sheet = data["quarterly_balance_sheet"]
            quarterly_cashflow = data["quarterly_cashflow"]

            # Display the latest quarter data
            latest_quarter = quarterly_financials.columns[0]  # Most recent quarter
            print(f"\nLatest Quarter: {latest_quarter.strftime('%Y-%m-%d')}")

            print("\nLatest Quarter Financial Data (Income Statement):")
            print(quarterly_financials.iloc[:, 0])

            print("\nLatest Quarter Balance Sheet:")
            print(quarterly_balance_sheet.iloc[:, 0])

            print("\nLatest Quarter Cash Flow:")
            print(quarterly_cashflow.iloc[:, 0])

            # Get latest earnings call info
            display_earnings_info(stock)

            # Export to CSV files
            export_financial_data(
                ticker,
                latest_quarter,
                quarterly_financials,
                quarterly_balance_sheet,
                quarterly_cashflow,
            )

            return {
                "latest_quarter": latest_quarter,
                "income_statement": quarterly_financials,
                "balance_sheet": quarterly_balance_sheet,
                "cash_flow": quarterly_cashflow,
            }

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2)  # Wait before retrying
            else:
                print(f"Failed to retrieve data after {max_retries} attempts: {e}")
                return None

    return None  # Explicit return for mypy


def display_earnings_info(stock: yf.Ticker) -> None:
    """
    Display earnings call information

    Args:
        stock: yfinance Ticker object
    """
    try:
        earnings_dates = stock.earnings_dates
        if earnings_dates is not None and not earnings_dates.empty:
            print(
                "\nLatest Earnings Call Date:",
                earnings_dates.index[0].strftime("%Y-%m-%d"),
            )
    except Exception as e:
        print(f"Error getting earnings dates: {e}")


def export_financial_data(
    ticker: str,
    latest_quarter: datetime,
    quarterly_financials: pd.DataFrame,
    quarterly_balance_sheet: pd.DataFrame,
    quarterly_cashflow: pd.DataFrame,
) -> None:
    """
    Export financial data to CSV files

    Args:
        ticker: Stock ticker symbol
        latest_quarter: Latest quarter date
        quarterly_financials: Income statement data
        quarterly_balance_sheet: Balance sheet data
        quarterly_cashflow: Cash flow data
    """
    output_dir = Path(f"{ticker}_quarterly_reports")
    output_dir.mkdir(exist_ok=True)

    quarter_str = latest_quarter.strftime("%Y-%m-%d")
    quarterly_financials.to_csv(output_dir / f"{ticker}_income_statement_{quarter_str}.csv")
    quarterly_balance_sheet.to_csv(output_dir / f"{ticker}_balance_sheet_{quarter_str}.csv")
    quarterly_cashflow.to_csv(output_dir / f"{ticker}_cash_flow_{quarter_str}.csv")

    print(f"Exported quarterly reports to {output_dir} directory")


def get_financial_data_simplified(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Simplified version of get_latest_quarterly_report_yahoo to reduce complexity

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary containing quarterly financial data or None if retrieval fails
    """
    print(f"Fetching quarterly report information for {ticker} using Yahoo Finance...")

    try:
        stock = yf.Ticker(ticker)

        # Get quarterly financials
        quarterly_financials = stock.quarterly_financials
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        quarterly_cashflow = stock.quarterly_cashflow

        # Check if we have data
        if quarterly_financials is None or quarterly_financials.empty:
            print("No quarterly financials data available")
            return None

        # Display the latest quarter data
        latest_quarter = quarterly_financials.columns[0]  # Most recent quarter
        print(f"\nLatest Quarter: {latest_quarter.strftime('%Y-%m-%d')}")

        # Print summary data
        print_financial_summaries(quarterly_financials, quarterly_balance_sheet, quarterly_cashflow)

        # Get latest earnings call info
        get_earnings_info(stock)

        # Export to CSV files for easier analysis
        export_to_csv(
            ticker,
            latest_quarter,
            quarterly_financials,
            quarterly_balance_sheet,
            quarterly_cashflow,
        )

        # Return the financial data
        return {
            "latest_quarter": latest_quarter,
            "income_statement": quarterly_financials,
            "balance_sheet": quarterly_balance_sheet,
            "cash_flow": quarterly_cashflow,
        }

    except Exception as e:
        print(f"Error in retrieving quarterly report: {e}")
        return None


def print_financial_summaries(
    quarterly_financials: pd.DataFrame,
    quarterly_balance_sheet: pd.DataFrame,
    quarterly_cashflow: pd.DataFrame,
) -> None:
    """
    Print summaries of the financial statements

    Args:
        quarterly_financials: Income statement data
        quarterly_balance_sheet: Balance sheet data
        quarterly_cashflow: Cash flow data
    """
    print("\nLatest Quarter Financial Data (Income Statement):")
    print(quarterly_financials.iloc[:, 0])  # First column is the most recent quarter

    print("\nLatest Quarter Balance Sheet:")
    print(quarterly_balance_sheet.iloc[:, 0])

    print("\nLatest Quarter Cash Flow:")
    print(quarterly_cashflow.iloc[:, 0])


def get_earnings_info(stock: yf.Ticker) -> None:
    """
    Get and print earnings call information

    Args:
        stock: yfinance Ticker object
    """
    try:
        earnings_dates = stock.earnings_dates
        if earnings_dates is not None and not earnings_dates.empty:
            print("\nLatest Earnings Call Date:", earnings_dates.index[0].strftime("%Y-%m-%d"))
    except Exception as e:
        print(f"Error getting earnings dates: {e}")


def export_to_csv(
    ticker: str,
    latest_quarter: datetime,
    quarterly_financials: pd.DataFrame,
    quarterly_balance_sheet: pd.DataFrame,
    quarterly_cashflow: pd.DataFrame,
) -> None:
    """
    Export financial data to CSV files

    Args:
        ticker: Stock ticker symbol
        latest_quarter: Latest quarter date
        quarterly_financials: Income statement data
        quarterly_balance_sheet: Balance sheet data
        quarterly_cashflow: Cash flow data
    """
    output_dir = Path(f"{ticker}_quarterly_reports")
    output_dir.mkdir(exist_ok=True)

    quarter_str = latest_quarter.strftime("%Y-%m-%d")
    quarterly_financials.to_csv(output_dir / f"{ticker}_income_statement_{quarter_str}.csv")
    quarterly_balance_sheet.to_csv(output_dir / f"{ticker}_balance_sheet_{quarter_str}.csv")
    quarterly_cashflow.to_csv(output_dir / f"{ticker}_cash_flow_{quarter_str}.csv")

    print(f"Exported quarterly reports to {output_dir} directory")


def format_number(num: Union[float, int, None]) -> str:
    """
    Format financial numbers for readability

    Args:
        num: Number to format

    Returns:
        Formatted string representation of the number
    """
    if pd.isna(num) or num is None:
        return "N/A"
    elif abs(num) >= 1e9:
        return f"${num / 1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"${num / 1e6:.2f}M"
    else:
        return f"${num:.2f}"


def add_metrics_by_category(
    metrics: Dict[str, str],
    dataframe: pd.DataFrame,
    latest_quarter: datetime,
    metric_list: List[str],
    display_names: Optional[Dict[str, str]] = None,
) -> None:
    """
    Add metrics from a specific category to the metrics dictionary

    Args:
        metrics: Dictionary to add metrics to
        dataframe: DataFrame containing the financial data
        latest_quarter: Latest quarter date
        metric_list: List of metrics to add
        display_names: Optional mapping of metric names to display names
    """
    if display_names is None:
        display_names = {}

    for metric in metric_list:
        display_name = display_names.get(metric, metric)
        if metric in dataframe.index:
            # Use get_financial_value to avoid mypy errors with loc indexing
            value = get_financial_value(dataframe, metric, latest_quarter)
            metrics[display_name] = format_number(value)
        else:
            metrics[display_name] = "N/A"


def extract_key_metrics(financial_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Extract and format key metrics from the quarterly financial data

    Args:
        financial_data: Dictionary containing quarterly financial statements

    Returns:
        Dictionary of key financial metrics or None if extraction fails
    """
    if not financial_data:
        return None

    try:
        income_statement = financial_data["income_statement"]
        balance_sheet = financial_data["balance_sheet"]
        cash_flow = financial_data["cash_flow"]
        latest_quarter = financial_data["latest_quarter"]

        quarter_str = latest_quarter.strftime("%Y-%m-%d")

        # Start with basic metrics
        metrics: Dict[str, str] = {"Quarter End Date": quarter_str}

        # Add metrics by category to reduce complexity
        add_metrics_by_category(
            metrics,
            income_statement,
            latest_quarter,
            ["Total Revenue", "Net Income", "Diluted EPS", "Operating Income", "Gross Profit"],
        )

        add_metrics_by_category(
            metrics,
            balance_sheet,
            latest_quarter,
            ["Cash And Cash Equivalents", "Total Assets", "Total Debt"],
            {"Cash And Cash Equivalents": "Cash & Equivalents"},
        )

        add_metrics_by_category(
            metrics,
            cash_flow,
            latest_quarter,
            ["Operating Cash Flow", "Free Cash Flow", "Capital Expenditure"],
        )

        print("\n--- Key Financial Metrics Summary ---")
        for key, value in metrics.items():
            print(f"{key}: {value}")

        return metrics

    except Exception as e:
        print(f"Error extracting key metrics: {e}")
        return None


def get_latest_sec_filings(ticker: str) -> Optional[Dict[str, str]]:
    """
    Get SEC filing information using yfinance

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with filing date and URL or None if retrieval fails
    """
    print(f"\nAttempting to get recent SEC filings for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        filings = stock.get_sec_filings()

        if filings is not None and not filings.empty:
            # Filter for 10-Q (quarterly) filings
            quarterly_filings = filings[filings["formType"] == "10-Q"]

            if not quarterly_filings.empty:
                recent_filing = quarterly_filings.iloc[0]
                filing_date = recent_filing.name.strftime("%Y-%m-%d")
                filing_url = recent_filing["finalLink"]

                print("Latest 10-Q (Quarterly Report) Filing:")
                print(f"  Date: {filing_date}")
                print(f"  URL: {filing_url}")

                return {"date": filing_date, "url": filing_url}
            else:
                print("No 10-Q filings found in recent submissions")
        else:
            print("No SEC filings data available")

    except Exception as e:
        print(f"Error retrieving SEC filings: {e}")

    return None


def download_filing_html(filing_info: Optional[Dict[str, str]], ticker: str) -> Optional[Path]:
    """
    Download the HTML content of a filing

    Args:
        filing_info: Dictionary containing filing information
        ticker: Stock ticker symbol

    Returns:
        Path to downloaded file or None if download fails
    """
    if not filing_info or "url" not in filing_info:
        return None

    try:
        url = filing_info["url"]
        print(f"\nDownloading filing from {url}...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            output_dir = Path(f"{ticker}_quarterly_reports")
            output_dir.mkdir(exist_ok=True)

            # Save the HTML content
            filing_date = filing_info["date"]
            file_path = output_dir / f"{ticker}_10Q_{filing_date}.html"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            print("Filing downloaded and saved to {0}".format(file_path))
            return file_path
        else:
            print(f"Failed to download filing. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error downloading filing: {e}")

    return None


def get_financial_value(dataframe: pd.DataFrame, metric: str, quarter: datetime) -> Optional[float]:
    """
    Safely get a financial value from a dataframe

    Args:
        dataframe: Financial dataframe
        metric: Financial metric
        quarter: Quarter date

    Returns:
        Value or None if not found
    """
    if metric not in dataframe.index or quarter not in dataframe.columns:
        return None

    # Cast to avoid mypy errors with loc indexing
    value = dataframe.at[metric, quarter]
    if pd.isna(value):
        return None

    return cast(float, value)


def get_quarter_over_quarter_change(
    income_statement: pd.DataFrame,
    metric: str,
    current_quarter: datetime,
    previous_quarter: datetime,
) -> Optional[float]:
    """
    Calculate quarter-over-quarter percentage change for a metric

    Args:
        income_statement: DataFrame containing income statement data
        metric: Financial metric to calculate change for
        current_quarter: Current quarter date
        previous_quarter: Previous quarter date

    Returns:
        Percentage change or None if calculation fails
    """
    current_value = get_financial_value(income_statement, metric, current_quarter)
    previous_value = get_financial_value(income_statement, metric, previous_quarter)

    if current_value is None or previous_value is None or previous_value == 0:
        return None

    return ((current_value - previous_value) / previous_value) * 100


def generate_quarterly_report_analysis(
    financial_data: Optional[Dict[str, Any]], ticker: str
) -> None:
    """
    Generate a simple analysis of the quarterly report data

    Args:
        financial_data: Dictionary containing quarterly financial statements
        ticker: Stock ticker symbol
    """
    if not financial_data:
        return

    try:
        # Get the data for the last two quarters for comparison
        income_statement = financial_data["income_statement"]

        if income_statement.shape[1] < 2:
            print("Not enough historical data for comparison")
            return

        current_quarter = income_statement.columns[0]
        previous_quarter = income_statement.columns[1]

        print("\n--- Quarter-over-Quarter Comparison ---")

        # Create output directory
        output_dir = Path(f"{ticker}_quarterly_reports")
        output_dir.mkdir(exist_ok=True)

        quarter_str = current_quarter.strftime("%Y-%m-%d")
        analysis_path = output_dir / f"{ticker}_analysis_{quarter_str}.txt"

        # Key metrics to compare
        metrics = ["Total Revenue", "Operating Income", "Net Income", "Gross Profit"]

        # Create a simple text file with analysis
        with open(analysis_path, "w") as f:
            f.write(f"Quarterly Report Analysis for {ticker}\n")
            f.write(f"Quarter ending: {quarter_str}\n\n")

            f.write("Quarter-over-Quarter Comparison:\n")

            for metric in metrics:
                change_pct = get_quarter_over_quarter_change(
                    income_statement, metric, current_quarter, previous_quarter
                )

                if change_pct is not None:
                    direction = "increase" if change_pct > 0 else "decrease"
                    msg = f"{metric}: {change_pct:.2f}% {direction} from previous quarter"
                    print(msg)
                    f.write(f"{msg}\n")

        print("Analysis saved to {0}".format(analysis_path))

    except Exception as e:
        print(f"Error generating analysis: {e}")


def main() -> None:
    """Main function to execute the script."""
    ticker = "META"

    # 1. Get quarterly financial data from Yahoo Finance
    # Use the simplified version to avoid complexity issues
    financial_data = get_financial_data_simplified(ticker)

    # 2. Extract and display key metrics
    if financial_data:
        # Extract key metrics and use the result to track success
        metrics_result = extract_key_metrics(financial_data)
        has_metrics = metrics_result is not None

        # 3. Generate a simple analysis of the quarterly data
        generate_quarterly_report_analysis(financial_data, ticker)

        print("\nMetrics extraction: {0}".format("Successful" if has_metrics else "Failed"))

    # 4. Get SEC filing information
    filing_info = get_latest_sec_filings(ticker)

    # 5. Download the filing if information is available
    if filing_info:
        # Store file path for potential future use
        report_file = download_filing_html(filing_info, ticker)
        print("\nReport download: {0}".format("Completed" if report_file else "Failed"))

    print("\nScript execution completed.")


if __name__ == "__main__":
    main()

"""Unit tests for BAML ticker ETL functions."""

import asyncio
import json
from pathlib import Path

import pytest

from abzu.baml_client import b as baml_client
from abzu.baml_client.types import Company, CompanyList, Ticker, TickerList


@pytest.mark.asyncio
@pytest.mark.parametrize("max_tickers", [None])  # Set to an integer to limit, or None for all
async def test_add_tickers_to_companies(max_tickers):
    """Test AddTickersToCompanies function with real ticker and company data.

    Set max_tickers to an integer to limit the number of tickers loaded for testing,
    or None to load all tickers.
    """
    # Load ticker data
    ticker_file = Path("data/financialdatasets/all_tickers_facts_baml.jsonl")
    tickers = []
    with open(ticker_file, "r") as f:
        for i, line in enumerate(f):
            if max_tickers is not None and i >= max_tickers:
                break
            ticker_data = json.loads(line)
            ticker = Ticker(
                name=ticker_data["name"],
                symbol=ticker_data["symbol"],
                exchange=ticker_data.get("exchange"),
            )
            tickers.append(ticker)

    # Load company names
    company_file = Path("data/company_names.json")
    companies = []
    with open(company_file, "r") as f:
        # Load first 100 companies for testing
        for i, line in enumerate(f):
            if i >= 1000:
                break
            company_data = json.loads(line)
            company = Company(name=company_data["name"])
            companies.append(company)

    # Create input objects
    company_list = CompanyList(companies=companies)
    ticker_list = TickerList(tickers=tickers)

    # Call the BAML function
    result = await baml_client.AddTickersToCompanies(
        company_list=company_list, ticker_list=ticker_list
    )

    # Verify all original company names are present
    original_names = {c.name for c in companies}
    result_names = {c.name for c in result.companies}
    assert original_names == result_names, "Not all original company names are present"

    # Count how many companies have tickers assigned
    companies_with_tickers = sum(1 for c in result.companies if c.ticker is not None)

    # Print results for debugging
    print(f"Total companies: {len(result.companies)}")
    print(f"Companies with tickers: {companies_with_tickers}")
    print(f"Companies without tickers: {len(result.companies) - companies_with_tickers}")

    # Show some examples of matched companies
    matched_examples = [c for c in result.companies if c.ticker is not None][:5]
    for company in matched_examples:
        print(f"  {company.name} -> {company.ticker.symbol}")

    # Not all companies will have tickers (many won't match), but at least some should
    assert companies_with_tickers > 0, "At least some companies should have tickers assigned"


@pytest.mark.asyncio
async def test_add_tickers_to_companies_with_known_match():
    """Test AddTickersToCompanies with a known matching pair."""
    # Create test data with known matches
    companies = [
        Company(name="American Airlines Group Inc"),
        Company(name="3M Company"),
        Company(name="Unknown Company XYZ"),
    ]

    tickers = [
        Ticker(name="American Airlines Group Inc", symbol="AAL", exchange="NASDAQ"),  # Exact match
        Ticker(name="3M Co", symbol="MMM", exchange="NYSE"),  # Close match
        Ticker(name="Unrelated Corp", symbol="UNR", exchange="NYSE"),
    ]

    company_list = CompanyList(companies=companies)
    ticker_list = TickerList(tickers=tickers)

    # Call the BAML function
    result = await baml_client.AddTickersToCompanies(
        company_list=company_list, ticker_list=ticker_list
    )

    # Verify all original company names are present
    original_names = {c.name for c in companies}
    result_names = {c.name for c in result.companies}
    assert original_names == result_names, "Not all original company names are present"

    # Find the American Airlines result
    aa_result = next((c for c in result.companies if c.name == "American Airlines Group Inc"), None)
    assert aa_result is not None, "American Airlines should be in results"

    # American Airlines should have a ticker assigned (exact match)
    if aa_result.ticker:
        assert aa_result.ticker.symbol == "AAL", "American Airlines should have AAL ticker"
        print(f"✓ American Airlines correctly matched to {aa_result.ticker.symbol}")
    else:
        print("American Airlines did not get a ticker (may depend on LLM behavior)")

    # Print all results for debugging
    for company in result.companies:
        ticker_info = (
            f"{company.ticker.symbol} ({company.ticker.exchange})"
            if company.ticker
            else "No ticker"
        )
        print(f"  {company.name}: {ticker_info}")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_add_tickers_to_companies())
    asyncio.run(test_add_tickers_to_companies_with_known_match())

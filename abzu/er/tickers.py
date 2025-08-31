import asyncio
import json
import logging
from pathlib import Path

from abzu.baml_client import b as baml_client
from abzu.baml_client.types import Company, CompanyList, Ticker, TickerList

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def add_tickers_to_companies_blocked():

    block_size = 1000
    all_results = []
    # total_with_tickers = 0

    ticker_file = Path("data/financialdatasets/all_tickers_facts_baml.jsonl")
    tickers = []
    with open(ticker_file, "r") as f:
        # Load first 100 tickers for testing
        for i, line in enumerate(f):
            # if i >= 100:
            #     break
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
            company_data = json.loads(line)
            company = Company(name=company_data["name"])
            companies.append(company)

    # Create input objects
    company_list = CompanyList(companies=companies)
    ticker_list = TickerList(tickers=tickers)

    for i in range(0, len(companies), block_size):
        # block_companies = companies[i : i + block_size]
        print(
            f"\nProcessing block {i // block_size + 1}: companies {i} to {min(i + block_size, len(companies))}"
        )
        # Call the BAML function
        result = await baml_client.AddTickersToCompanies(
            company_list=company_list, ticker_list=ticker_list
        )

        all_results.extend(result.companies)

        # Show some examples of matched companies
        matched_examples = [c for c in result.companies if c.ticker is not None][:5]
        for company in matched_examples:
            logger.debug(f"{company.name} -> {company.ticker.symbol}")

        # Count how many companies have tickers assigned
        companies_with_tickers = sum(1 for c in result.companies if c.ticker is not None)

        # Print results for debugging
        print(f"Total companies: {len(result.companies)}")
        print(f"Companies with tickers: {companies_with_tickers}")
        print(f"Companies without tickers: {len(result.companies) - companies_with_tickers}")

        return all_results


if __name__ == "__main__":
    # Run the tests
    companies_with_tickers = asyncio.run(add_tickers_to_companies_blocked())

    with open("data/financialdatasets/companies_with_tickers.jsonl", "w") as f:
        for company in companies_with_tickers:
            f.write(json.dumps(company.to_dict()) + "\n")

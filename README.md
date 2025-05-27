# Abzu

A Knowledge Graph Bloomberg Terminal™ + Waters of wisdom... knowledge graph of silicon.

<center><img src="images/Akka-Seal-Enki-Abzu.jpg" width="500px" alt="The Akka Seal showing Enki with the Abzu flowing out from him."/></center>

## Abzu Steps

The `abzu steps` command that installs via `poetry install` will describe the steps required to build the knowledge graph.

```bash
abzu steps
```

## Project Setup

### Create Python Environment

```bash
# Conda environment
conda create -n abzu python=3.12 -y
conda activate abzu

# Virtualenv
python -m venv venv
source venv/bin/activate
```

### Option 1: Install `poetry` with `pipx`

```bash
# Install pipx on OS X
brew install pipx

# Install pipx on Ubuntu
sudo apt update
sudo apt install -y pipx

# Install poetry
pipx install poetry
```

### Option 2: Install `poetry` with 'Official Installer'

```bash
# Try pipx if your firewall prevents this...
curl -sSL https://install.python-poetry.org | python3 -
```

### Install Python Dependencies

```bash
# Install dependencies
poetry install
```

### Install Pre-Commit Checks

```bash
# black, isort, flake8, mypy
pre-commit install
```

### Generate BAML Client for Python

```bash
# To rebuild abzu.baml_client
# NOTE: make sure your plugin and baml-py versions match!
baml-cli test
baml-cli generate
```

## Crawl

Crawl SemiAnalysis.com or TheInformation.com:

```bash
# SemiAnalysis
abzu crawl semianalysis

# TheInformation (requires login cookies)
abzu crawl theinformation
# Generic RSS feeds from feeds.txt
abzu crawl rss -f feeds.txt
# Outputs to the directory configured in `crawl.rss.output_dir`
```

To scrape TheInformation you must be signed into the site in your browser so the
command can load your session cookies. Alternatively pass `--cookie "name=value;"`
to the command.
The crawler fetches from `https://www.theinformation.com/feed` by default.

## Information Extraction

Run the information extraction via the [VSCode Plugin](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension):

```bash
# Setup Gemini key
export GEMINI_API_KEY="<gemini API key>"

baml-cli generate

# To run the test data
baml-cli test

# To extract BAML types from SemiAnalysis.com articles
abzu process articles semianalysis
# To extract BAML types from TheInformation.com articles
abzu process articles theinformation
# To process articles downloaded via feeds.txt
abzu process rss -f feeds.txt
# Processed articles are saved in data/processed_theinformation.jsonl

# Extract each vertex / edge into its own Parquet
abzu process kg raw
# Uses data/processed_semianalysis.jsonl and data/processed_theinformation.jsonl

# To enrich with FinancialDatasets.ai company facts TODO: make this the default path
abzu api financialdatasets --file data/knowledge_graph/tickers.parquet
# Get historical price data for all tickers and show the best performers
abzu api financialdatasets price -f data/knowledge_graph/tickers.parquet -s 2025-01-01 -e 2025-12-31 -i day -o data/financialdatasets/all_prices.json
abzu dump returns -f data/financialdatasets/all_prices.json

# Get historical price data for tickers
abzu api financialdatasets price -f -s 2023-01-01 -e 2023-12-31
# Or for a single ticker
abzu api financialdatasets price -t AAPL -s 2023-01-01 -e 2023-12-31

# Create a combined vertex / edge list
abzu process kg refine
abzu dump products -f data/refined_knowledge_graph/products.parquet
# Products are listed sorted by company name

# Download SEC filings for all tickers
abzu api sec download
```

## Dataflow + KG Schemas

### Articles

```json
{
    "url": "https://semianalysis.com/2021/06/21/globalfoundries-is-a-leading-edge/",
    "list_url": "https://semianalysis.com/archives/page/23/",
    "title": "GlobalFoundries Is A Leading-Edge Foundry Despite Claims Otherwise – SemiAnalysis",
    "posted_at": "2021-06-21T19:19:48+00:00",
    "collected_at": "2025-04-15T04:20:37.763490",
    "content": "GlobalFoundries is still a..."
}
```

### FinancialDatasets.ai Company Facts

```json
{
  "company_facts": {
    "ticker": "WOLF",
    "name": "Wolfspeed Inc",
    "cik": "0000895419",
    "industry": "Semiconductors",
    "sector": "Technology",
    "category": "Common Stock",
    "exchange": "NYSE",
    "is_active": true,
    "listing_date": "1993-02-09",
    "location": "North Carolina; U.S.A",
    "market_cap": 488493323.08000004,
    "number_of_employees": 5013,
    "sec_filings_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000895419",
    "sic_code": "3674.0",
    "sic_industry": "Semiconductors & Related Devices",
    "sic_sector": "Manufacturing",
    "website_url": "https://www.wolfspeed.com",
    "weighted_average_shares": 155571122
  },
  "request": {
    "ticker": "WOLF",
    "cik": null
  }
}
```

### Knowledge Graph Parquet

Vertices:

```sql
                           id entity_type                                           properties
0     Applied Materials, Inc.     company  {"description":"A semiconductor equipment comp..."}
1                    Spectra7     company  {"description":"Firm in the AEC and ACC produc..."}
2                       Macom     company  {"description":"A provider of TIAs and other a..."}
3                     Vedanta     company  {"description":"An Indian multinational corpor..."}
4                Xilinx, Inc.     company  {"description":"Xilinx is a company that speci..."}
...                       ...         ...                                                ...
1164                     AIXA      ticker                   {"name":"Aixtron","symbol":"AIXA"}
1165                     NVDA      ticker                    {"name":"Nvidia","symbol":"NVDA"}
1166                     ASML      ticker                      {"name":"ASML","symbol":"ASML"}
1167                     TSLA      ticker                     {"name":"Tesla","symbol":"TSLA"}
1168                     6857      ticker  {"exchange":"JP","name":"Advantest","symbol":"..."}
```

Node Types:

```sql
              id  properties
entity_type                 
company      354         354
product      411         411
technology   356         356
ticker        48          48
```

Edges:

```sql
                                         src                           dst relationship
0                                     Nvidia               Bluefield-3 DPU        Sells
1                                     Nvidia    Base Command Manager (BCM)        Sells
2                                      Intel                 Sierra Forest        Sells
3                                     Nvidia                          A100        Sells
4               Advanced Micro Devices, Inc.                       Navi 32        Sells
...                                      ...                           ...          ...
1575                      Advanced Packaging                         Veeco  DevelopedBy
1576                                     7nm                          SMIC  DevelopedBy
1577  Wavelength-division multiplexing (WDM)                        Google  DevelopedBy
1578                        Zen architecture  Advanced Micro Devices, Inc.  DevelopedBy
1579                              NeuronLink                           AWS  DevelopedBy
```

Edge Types:

```sql
              src  dst
relationship          
DevelopedBy   356  356
Develops      356  356
ListedUnder    23   23
Represents     23   23
Sells         411  411
SoldBy        411  411
```

## HOWTO `poetry`

```bash
# Install dependencies
poetry install
```

```bash
# Add dependency
poetry add <pypi package name>
```

```bash
# Remove dependency
poetry remove <pypi package name>
```

```bash
# Update libraries to latest and re-read pyproject.toml after edits
poetry update
```

## Configuration and External Strings

We store configuration and external strings in the `config.yml` file. These can be loaded via the `abzu.config` module.

```python
from abzu.config import config

# Access a configuration value
value = config.get("some_key", "default_value")
```

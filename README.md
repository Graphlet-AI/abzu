# Abzu

A Knowledge Graph Bloomberg Terminal™ + Waters of wisdom... knowledge graph of silicon.

<center><img src="images/Akka-Seal-Enki-Abzu.jpg" width="500px" alt="The Akka Seal showing Enki with the Abzu flowing out from him."/></center>

## Quick Start

### System Requirements

- Python 3.12
- Java 11 (for Apache Spark)
- Apache Spark 3.5+
- 4GB+ RAM recommended (for Spark processing)

### Initial Setup

1. Clone the repository:

```bash
git clone https://github.com/abzuc/abzu.git
cd abzu
```

2. Run the CLI to see the features the app has:

```bash
./abzu --help
```

3. Run commands:

```bash
# Show help
abzu --help

# Run crawler
abzu crawl semianalysis -b 10

# Process articles
abzu process articles semianalysis

# Process knowledge graph
abzu process kg raw
```

## Local Setup

You can set up the project directly on your machine.

### Pre-Requisites

1. Python 3.12
2. Java 11
3. Apache Spark 3.5+

### Installation Steps

0. Install pqrs (if not already installed) to inspect Parquet files:

```bash
# Install Rust util pqrs to inspect Parquet files
brew install manojkarthick/tap/pqrs
```

1. Create a Python environment:

```bash
# Option 1: Conda
conda create -n abzu python=3.12 -y
conda activate abzu

# Option 2: Virtualenv
python -m venv venv
source venv/bin/activate
```

2. Install Poetry:

```bash
# Option 1: Using pipx (recommended)
# On macOS:
brew install pipx
# On Ubuntu:
sudo apt update
sudo apt install -y pipx

pipx install poetry

# Option 2: Using official installer
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:

```bash
poetry install
```

4. Install pre-commit checks:

```bash
pre-commit install
```

5. Generate BAML client:

```bash
baml-cli test
baml-cli generate
```

6. Install the PlayWright browsers:

```bash
playwright install
```

### Running Locally

Once installed, you can run commands directly:

```bash
# Show help
abzu --help

# Run crawler
abzu crawl semianalysis

# Process articles
abzu process articles semianalysis

# Process knowledge graph
abzu process kg raw

# Entity resolution
abzu process er all --iteration 1 -m 50 -b 40
abzu process er all --iteration 2 -m 50 -b 40
abzu process er all --iteration 3 -m 50 -b 40
abzu process er all --iteration 4 -m 50 -b 40
abzu process er all --iteration 5 -m 50 -b 40
```

## Spark Processing Modes

The application supports two Spark processing modes:

1. **Local Mode (Default)**

   - Runs Spark in a single JVM on your machine
   - Best for:
     - Development and testing
     - Small to medium datasets
     - Quick iterations and debugging
   - Configuration:
     - Uses all available CPU cores
     - Configurable memory settings (default: 4GB driver, 2GB executor)
     - No additional services required

2. **Distributed Mode (Docker only)**

   - Runs Spark across multiple containers using Bitnami Spark images
   - Best for:
     - Production environments
     - Large datasets
     - Complex graph operations
   - Features:
     - Single worker with 2 cores and 2GB memory
     - Web UI monitoring (ports 18080, 18081)
     - Fault tolerance
   - Configuration:
     - Master UI: <http://localhost:18080>
     - Worker UI: <http://localhost:18081>
     - Worker resources: 2 cores, 2GB memory

### Monitoring and Debugging

1. **Local Mode**:

   - Logs appear in your terminal
   - Memory usage visible in system monitor
   - Easy to debug with print statements

2. **Distributed Mode**:

   - Spark UI available at `http://localhost:18080`
   - Worker UI at `http://localhost:18081`
   - Monitor:
     - Job progress
     - Memory usage
     - Task distribution
     - Worker status

## Environment Variables

Add your API keys to `docker-compose.yml` for Docker setup:

```yaml
environment:
  - GEMINI_API_KEY=your_key_here
  # Add other API keys as needed
```

For local setup, set environment variables in your shell:

```bash
export GEMINI_API_KEY="your_key_here"
```

## Project Structure

```
weave/
├── abzu/               # Main package
│   ├── api/           # External API integrations
│   ├── articles/      # Article processing
│   ├── chat/          # Chat functionality
│   ├── cli/           # Command-line interface
│   ├── crawl/         # Web crawling
│   ├── kg/            # Knowledge graph
│   └── spark/         # Data processing
├── baml_src/          # BAML definitions
├── data/              # Data storage
└── tests/             # Test suite
```

## Common Tasks

### Crawling SemiAnalysis.com, reddit, or TheInformation.com

```bash
# Docker (in container shell)
# SemiAnalysis
poetry run abzu crawl semianalysis

# TheInformation (requires login cookies)
poetry run abzu crawl theinformation
# Generic RSS feeds from feeds.txt
poetry run abzu crawl rss -f feeds.txt

 # Reddit - fetch ticker discussions
abzu crawl reddit ticker AAPL
abzu crawl reddit ticker TSLA --limit 50
abzu crawl reddit ticker NVDA --output data/nvidia_reddit.jsonl

# Local Installed Example (not docker)
# SemiAnalysis
abzu crawl semianalysis
# TheInformation (requires login cookies)
abzu crawl theinformation
# Generic RSS feeds from feeds.txt
abzu crawl rss
# Outputs to the directory configured in `crawl.rss.output_dir`
```

To scrape TheInformation you must be signed into the site in your browser so the command can load your session cookies. Alternatively pass `--cookie "name=value;"` to the command. The crawler fetches from `https://www.theinformation.com/feed` by default.

### Information Extraction

Run the information extraction via the [VSCode Plugin](https://marketplace.visualstudio.com/items?itemName=Boundary.baml-extension):

#### Docker Setup

````bash
# Inside container shell
# Generate BAML client code
baml-cli generate

# Test BAML definitions
baml-cli test

# Process articles to extract BAML types from the SemiAnalysis.com articles
poetry run abzu process articles semianalysis
# Process articles to extract BAML types from TheInformation.com articles
poetry run abzu process articles theinformation
# Processed articles are saved in data/processed_theinformation.jsonl

> **Tip**: TheInformation.com requires authentication to access their content. There are two ways to handle this:
>
> 1. **Local Environment**: If you're signed into TheInformation.com in Chrome, the crawler will automatically use your browser's cookies. No additional setup needed.
>
> 2. **Docker Container**: Since the container can't access your browser's cookies, you need to manually provide them:
>    ```bash
>    # First, extract cookies from your local browser:
>    # Chrome/Edge: Open DevTools (F12) -> Application -> Cookies -> theinformation.com
>    # Firefox: Open DevTools (F12) -> Storage -> Cookies -> theinformation.com
>    # Copy the cookie string
>
>    # Then run the crawler with the cookies in the container:
>    poetry run abzu process articles theinformation --cookie "name=value;"
>    ```
>
> The crawler fetches from `https://www.theinformation.com/feed` by default.

# Extract each vertex / edge into its own Parquet
poetry run abzu process kg raw
# Uses data/processed_semianalysis.jsonl and data/processed_theinformation.jsonl
poetry run abzu process kg refine
````

#### Local Setup

```bash
# Set up Gemini API key
export GEMINI_API_KEY="<gemini API key>"

# Generate BAML client code
baml-cli generate

# Test BAML definitions
baml-cli test

# Process articles
abzu process articles semianalysis
abzu process articles theinformation
# To process articles downloaded via feeds.txt
abzu process rss -f feeds.txt
# Processed articles are saved in data/processed_theinformation.jsonl

# Extract each vertex / edge into its own Parquet
abzu process kg raw
# Uses data/processed_semianalysis.jsonl and data/processed_theinformation.jsonl
abzu process kg refine
```

Note: For Docker setup, the Gemini API key should be configured in `docker-compose.yml`:

```yaml
environment:
  - GEMINI_API_KEY=your_key_here
```

### API Operations

```bash
# Docker (in container shell)
poetry run abzu api financialdatasets facts -f
# Get historical price data for all tickers and show the best performers
poetry run abzu api financialdatasets price -f -s 2025-01-01 -e 2025-12-31 -i day -o data/financialdatasets/all_prices.json
poetry run abzu dump returns -f data/financialdatasets/all_prices.json

# Get historical price data for tickers
poetry run abzu api financialdatasets price -f -s 2023-01-01 -e 2023-12-31
# Or for a single ticker
poetry run abzu api financialdatasets price -t AAPL -s 2023-01-01 -e 2023-12-31

# Create a combined vertex / edge list
poetry run abzu process kg refine
# SEC ticker symbols are automatically added when matches are exact
poetry run abzu dump products -f data/refined_knowledge_graph/products.parquet
# Review ticker matches for companies without tickers (exact matches are applied)
poetry run abzu dump company-ticker-resolution -f data/refined_knowledge_graph/companies.parquet
# Products are listed sorted by company name

# Download SEC filings for all tickers
poetry run abzu api sec download
# Or for a single ticker
poetry run abzu api sec download --ticker NVDA
# Download a single annual report and process it with BAML
poetry run abzu api sec annual-report --ticker NVDA --year 2023
poetry run abzu api sec annual-report --ticker NVDA --year 2023 --bfs
poetry run abzu api sec annual-reports build kuzu
poetry run abzu api sec annual-reports bulk
# Output files are written to config.api.sec.build_kuzu.output_dir:
# - companies.csv
# - invests_in.csv
# - has_investor.csv
# - partnered_with.csv
# - supplies.csv
# - has_supplier.csv
# - subsidiary_of.csv
# - has_subsidiary.csv

# Local
abzu api financialdatasets facts -f
abzu api financialdatasets price -t AAPL -s 2023-01-01 -e 2023-12-31
abzu api sec download
```

## Data Schemas

### Articles

```json
{
  "url": "https://semianalysis.com/2021/06/21/globalfoundries-is-a-leading-edge/",
  "list_url": "https://semianalysis.com/archives/page/23/",
  "title": "GlobalFoundries Is A Leading-Edge Foundry Despite Claims Otherwise – SemiAnalysis",
  "posted_at": "2021-06-21T19:19:48+00:00",
  "collected_at": "2025-04-15T04:20:37.763490",
  "content": "GlobalFoundries is still a...",
  "urls": [
    "https://fuse.wikichip.org/news/5588/a-look-at-trishul-arms-first-high-density-3d-logic-stacked-test-chip/"
  ]
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

## Logging

Abzu uses a centralized logging system that writes to both file and console.

### Usage

```python
from abzu.logs import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use standard logging methods
logger.info("Processing started")
logger.error(f"Failed to process: {error}")
logger.warning("Missing data")
logger.debug("Debug information")
```

### Configuration

Logging is configured in `config.yml`:

```yaml
logs:
  file:
    path: "${base_dir}/logs" # Logs stored in data/logs/
```

### Log Output

- **File**: Logs are written to `data/logs/app.log`
- **Console**: Logs are also displayed in the terminal
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Level**: INFO by default

### Best Practices

1. Always use `get_logger(__name__)` to create module-specific loggers
2. Use appropriate log levels:

   - `DEBUG`: Detailed information for diagnosing problems
   - `INFO`: General informational messages
   - `WARNING`: Warning messages for potentially harmful situations
   - `ERROR`: Error messages for serious problems
   - `CRITICAL`: Critical messages for very serious errors

3. Include context in error messages:

   ```python
   logger.error(f"Failed to process file {file_path}: {e}")
   ```

## HOWTO `poetry`

```bash
# Install dependencies
poetry install

# Add dependency
poetry add <pypi package name>

# Remove dependency
poetry remove <pypi package name>

# Update libraries to latest and re-read pyproject.toml after edits
poetry update
```

## Configuration

We store configuration and external strings in the `config.yml` file. These can be loaded via the `abzu.config` module.

```python
from abzu.config import config

# Access a configuration value
value = config.get("some_key", "default_value")
```

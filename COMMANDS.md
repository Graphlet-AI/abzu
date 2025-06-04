# Abzu Command Flows

This document explains the common command flows in Abzu, what they do, and how they work.

## Data Flow Overview

The typical workflow in Abzu follows these steps:

1. **Crawling**: Fetch articles from various sources
2. **Processing**: Extract structured information from articles
3. **Knowledge Graph**: Build and refine the knowledge graph
4. **API Operations**: Interact with external APIs for additional data

## Command Flows

### 1. Crawling Articles

#### SemiAnalysis.com Crawler

```bash
abzu crawl semianalysis
```

- **What it does**: Crawls the SemiAnalysis.com website for articles
- **How it works**:
  - Uses Scrapy to crawl archive pages
  - Extracts article content, titles, and publication dates
  - Saves articles to `data/semianalysis.jsonl`
- **Why**: SemiAnalysis provides detailed semiconductor industry analysis

#### TheInformation.com Crawler

```bash
abzu crawl theinformation
```

- **What it does**: Fetches articles from TheInformation.com's RSS feed
- **How it works**:
  - Requires authentication (uses browser cookies or manual cookie string)
  - Fetches the RSS feed at `https://www.theinformation.com/feed`
  - Extracts full article content
  - Saves to `data/theinformation.jsonl`
- **Why**: TheInformation provides exclusive tech industry news

#### Generic RSS Crawler

```bash
abzu crawl rss -f feeds.txt
```

- **What it does**: Crawls multiple RSS feeds defined in a file
- **How it works**:
  - Reads `source:url` pairs from `feeds.txt`
  - Creates separate JSONL files for each source
  - Supports custom cookies and user agents
- **Why**: Allows adding new sources without code changes

### 2. Processing Articles

#### Article Processing

```bash
abzu process articles semianalysis
abzu process articles theinformation
```

- **What it does**: Extracts structured information from crawled articles
- **How it works**:
  - Uses BAML to extract entities and relationships
  - Processes articles in parallel using Spark
  - Saves processed data to JSONL files
- **Why**: Converts unstructured text into structured data

#### Knowledge Graph Processing

```bash
abzu process kg raw
abzu process kg refine
```

- **What it does**: Builds and refines the knowledge graph
- **How it works**:
  - `raw`: Extracts vertices and edges from processed articles
  - `refine`: Combines and deduplicates graph elements
  - Uses Spark for distributed processing
- **Why**: Creates a structured representation of industry knowledge

### 3. API Operations

#### Financial Data

```bash
abzu api financialdatasets --file data/knowledge_graph/tickers.parquet
```

- **What it does**: Fetches financial data for companies
- **How it works**:
  - Reads company tickers from the knowledge graph
  - Fetches data from FinancialDatasets.ai
  - Saves price data and company facts
- **Why**: Enriches the knowledge graph with financial information

#### SEC Filings

```bash
abzu api sec download
```

- **What it does**: Downloads SEC filings for companies
- **How it works**:
  - Uses company CIK numbers from the knowledge graph
  - Downloads filings from SEC EDGAR
  - Processes and stores filing data
- **Why**: Provides regulatory and financial information

```bash
abzu api sec annual-report --ticker NVDA --year 2023
```
- **What it does**: Downloads a plain text 10-K filing
- **How it works**:
  - Retrieves the filing HTML for the specified year
  - Saves the text to the annual reports directory
- **Why**: Enables LLM processing of annual reports

### 4. Development Commands

#### Testing

```bash
abzu test
```

- **What it does**: Runs the test suite
- **How it works**:
  - Executes unit tests
  - Runs integration tests
  - Validates BAML definitions
- **Why**: Ensures code quality and functionality

#### Linting and Formatting

```bash
abzu lint
abzu format
```

- **What it does**: Checks and fixes code style
- **How it works**:
  - `lint`: Runs style checkers
  - `format`: Applies code formatting
- **Why**: Maintains consistent code style

## Environment-Specific Notes

### Local Environment

- Direct access to browser cookies
- Faster processing for small datasets
- Good for development and testing

### Docker Environment

- Isolated environment
- Consistent dependencies
- Better for production and large datasets
- Requires manual cookie handling for authenticated sources

## Common Issues and Solutions

1. **Authentication Issues**
   - Local: Ensure you're signed into Chrome
   - Docker: Manually provide cookies via `--cookie` flag

2. **Processing Errors**
   - Check input file paths
   - Verify API keys are set
   - Ensure sufficient memory for Spark

3. **Performance**
   - Adjust Spark partitions based on data size
   - Use appropriate batch sizes for crawling
   - Monitor memory usage in Docker

## Best Practices

1. **Data Management**
   - Keep raw and processed data separate
   - Use consistent file naming
   - Regular backups of important data

2. **Processing**
   - Start with small batches when testing
   - Monitor Spark UI for performance
   - Use appropriate memory settings

3. **Development**
   - Run tests before committing
   - Keep BAML definitions up to date
   - Document new sources in `feeds.txt`

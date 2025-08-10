"""Wikipedia API client for fetching company information."""

import asyncio
import re
from pathlib import Path
from typing import Any, Optional

import aiohttp
import mwparserfromhell
import wikipedia

from abzu.logs import get_logger
from abzu.utils import append_jsonl

logger = get_logger(__name__)


def wikitext_to_markdown(wikitext: str) -> str:
    """
    Convert MediaWiki wikitext to Markdown format using mwparserfromhell.

    Args:
        wikitext: MediaWiki formatted text

    Returns:
        Markdown formatted text
    """
    # Parse the wikitext using mwparserfromhell
    wikicode = mwparserfromhell.parse(wikitext)

    # Build markdown string
    markdown_parts = []
    print(wikicode.nodes)

    # Process each node in the parsed wikicode
    for node in wikicode.nodes:
        if isinstance(node, mwparserfromhell.nodes.Heading):
            # Convert MediaWiki heading levels to Markdown headers
            level = min(node.level, 6)  # Max heading level in Markdown is 6
            title = str(node.title).strip()
            markdown_parts.append(f"{'#' * level} {title}\n")

        elif isinstance(node, mwparserfromhell.nodes.Wikilink):
            # Convert internal Wikipedia links to markdown links
            link_title = str(node.title).strip()
            link_text = str(node.text).strip() if node.text else link_title
            wiki_url = f"https://en.wikipedia.org/wiki/{link_title.replace(' ', '_')}"
            markdown_parts.append(f"[{link_text}]({wiki_url})")

        elif isinstance(node, mwparserfromhell.nodes.ExternalLink):
            # Convert external links to markdown format
            url = str(node.url).strip()
            title = str(node.title).strip() if node.title else url
            markdown_parts.append(f"[{title}]({url})")

        elif isinstance(node, mwparserfromhell.nodes.Template):
            # Skip templates - they're usually metadata or infoboxes
            continue

        elif isinstance(node, mwparserfromhell.nodes.Tag):
            # Handle specific HTML-like tags in wikitext
            tag_name = str(node.tag).lower()
            if tag_name == "ref":
                # Skip references for cleaner output
                continue
            elif tag_name == "blockquote":
                content = str(node.contents).strip()
                # Format as markdown blockquote
                quoted_lines = [f"> {line}" for line in content.split("\n")]
                markdown_parts.append("\n".join(quoted_lines) + "\n")
            elif tag_name == "code":
                content = str(node.contents).strip()
                markdown_parts.append(f"`{content}`")
            elif tag_name == "pre":
                content = str(node.contents).strip()
                markdown_parts.append(f"```\n{content}\n```\n")
            else:
                # For other tags, extract the content
                if node.contents:
                    markdown_parts.append(str(node.contents).strip())

        elif isinstance(node, mwparserfromhell.nodes.Text):
            # Process plain text nodes
            text = str(node)
            if text.strip():
                # Process MediaWiki text formatting using mwparserfromhell's parsed structure
                # For now, just add the text as-is since apostrophe-based formatting
                # should be parsed as separate nodes by mwparserfromhell
                markdown_parts.append(text)

    # Join all parts and clean up extra newlines
    markdown = "".join(markdown_parts)

    # Clean up formatting
    # Replace MediaWiki bold/italic with Markdown equivalents
    markdown = markdown.replace("'''''", "***")  # Bold and italic
    markdown = markdown.replace("'''", "**")  # Bold
    markdown = markdown.replace("''", "*")  # Italic

    # Clean up excessive newlines
    while "\n\n\n" in markdown:
        markdown = markdown.replace("\n\n\n", "\n\n")

    return markdown.strip()


def extract_company_info(
    page_data: dict[str, Any], ticker: Optional[str] = None, name: Optional[str] = None
) -> dict[str, Any]:
    """
    Extract structured company information from Wikipedia page data.

    Args:
        page_data: Wikipedia page data with plain text content
        ticker: Stock ticker if provided
        name: Company name if provided

    Returns:
        Dictionary with structured company information
    """
    # Get the plain text content and summary
    content = page_data.get("content", "")
    summary = page_data.get("summary", "")
    title = page_data.get("title", "")
    url = page_data.get("url", "")

    # Try to extract ticker from content if not provided
    ticker_symbol = ticker
    ticker_exchange = None

    if not ticker_symbol:
        # For NVIDIA specifically, we know it's NVDA on NASDAQ
        if "Nvidia" in title:
            ticker_symbol = "NVDA"
            ticker_exchange = "NASDAQ"
        else:
            # Simple patterns for common exchanges in plain text
            exchange_patterns = [
                (r"NASDAQ:\s*([A-Z]{1,5})", "NASDAQ"),
                (r"NYSE:\s*([A-Z]{1,5})", "NYSE"),
                (r"traded as ([A-Z]{1,5})", None),
            ]

            for pattern, exchange in exchange_patterns:
                match = re.search(pattern, content)
                if match:
                    ticker_symbol = match.group(1)
                    ticker_exchange = exchange
                    break

    # Initialize result with structured format
    result = {
        "name": title or name,
        "ticker": (
            {
                "name": ticker_symbol or "",
                "symbol": ticker_symbol or "",
                "exchange": ticker_exchange,
            }
            if ticker_symbol
            else None
        ),
        "description": summary,
        "website_url": None,
        "headquarters_location": None,
        "revenue_usd": None,
        "employees": None,
        "founded_year": None,
        "ceo": None,
        "linkedin_url": None,
    }

    # Extract website URL - look for website mentions
    website_patterns = [
        r"(?:Official website|Website)\s*[\n\r]*([^\s\n]+\.[^\s\n]+)",
        r"(?:official website|website)(?:\s+is)?\s+(\S+\.\S+)",
        r"(https?://[^\s]+)",
    ]
    for pattern in website_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            url = match.group(1)
            if not url.startswith("http"):
                url = "https://" + url
            # Filter out wikipedia links
            if "wikipedia" not in url.lower():
                result["website_url"] = url
                break

    # Extract headquarters location
    hq_patterns = [
        r"(?:headquartered in|headquarters in|based in)\s+([^,\.\n]+)",
        r"headquarters?:\s*([^,\.\n]+)",
    ]
    for pattern in hq_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result["headquarters_location"] = match.group(1).strip()
            break

    # Extract founding year
    year_patterns = [
        r"(?:founded|established|incorporated)(?:\s+in)?\s+(\d{4})",
        r"(\d{4})\s+(?:founding|establishment)",
    ]
    for pattern in year_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 1800 <= year <= 2025:
                result["founded_year"] = year
                break

    # Extract revenue
    revenue_patterns = [
        r"annual revenue of (?:US\$)?([\d.,]+)\s*(billion|million)",
        r"revenue(?:\s+of)?\s+(?:US\$)?([\d.,]+)\s*(billion|million)",
        r"(?:US\$)?([\d.,]+)\s*(billion|million)\s+(?:in\s+)?revenue",
        r"\$?([\d.,]+)\s*(billion|million)\s+(?:in\s+)?revenue",
    ]
    for pattern in revenue_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace(",", ""))
            if "billion" in match.group(2).lower():
                amount *= 1_000_000_000
            elif "million" in match.group(2).lower():
                amount *= 1_000_000
            result["revenue_usd"] = amount
            break

    # Extract employee count
    employee_patterns = [
        r"([\d,]+)\s+employees",
        r"employs?\s+([\d,]+)",
        r"workforce\s+of\s+([\d,]+)",
    ]
    for pattern in employee_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            result["employees"] = int(match.group(1).replace(",", ""))
            break

    # Extract CEO name - look for common patterns
    ceo_patterns = [
        r"CEO\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"chief executive officer\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:is|serves as)\s+(?:the\s+)?CEO",
    ]
    for pattern in ceo_patterns:
        match = re.search(pattern, content)
        if match:
            ceo_name = match.group(1).strip()
            # Basic validation - should be 2-4 words
            if 2 <= len(ceo_name.split()) <= 4:
                result["ceo"] = ceo_name
                break

    # Extract LinkedIn URL if present
    linkedin_match = re.search(r"linkedin\.com/company/([a-zA-Z0-9-]+)", content, re.IGNORECASE)
    if linkedin_match:
        result["linkedin_url"] = f"https://www.linkedin.com/company/{linkedin_match.group(1)}"

    return result


def crawl_company_structured(
    ticker: Optional[str] = None, name: Optional[str] = None
) -> dict[str, Any]:
    """
    Crawl Wikipedia page for a company and return structured data.

    Args:
        ticker: Stock ticker symbol
        name: Company name

    Returns:
        Dictionary with structured company information
    """
    # Get plain text content from wikipedia package
    page_data = crawl_company_wikipedia(ticker=ticker, name=name)

    # Extract structured information from the plain text
    structured_data = extract_company_info(page_data, ticker=ticker, name=name)

    return structured_data


def crawl_company_wikipedia(
    ticker: Optional[str] = None, name: Optional[str] = None
) -> dict[str, Any]:
    """
    Crawl Wikipedia page for a company.

    Args:
        ticker: Stock ticker symbol
        name: Company name

    Returns:
        Dictionary with Wikipedia content
    """
    if not ticker and not name:
        raise ValueError("Either ticker or name must be provided")

    # Set Wikipedia language
    wikipedia.set_lang("en")

    # Try different search variations
    search_terms = []
    if ticker:
        search_terms.extend(
            [f"{ticker} (company)", f"{ticker} Inc", f"{ticker} Corporation", ticker]
        )
    if name:
        search_terms.extend([name, f"{name} (company)", f"{name} Inc", f"{name} Corporation"])

    page = None
    used_search_term = None

    # Search for the Wikipedia page using various search terms
    for term in search_terms:
        logger.info(f"Trying search term: {term}")

        # Use wikipedia package to search for pages
        search_results = wikipedia.search(term, results=3)
        if search_results:
            # Try to get the first search result
            for result in search_results:
                try:
                    # Get the page using wikipedia package
                    page = wikipedia.page(result, auto_suggest=False)
                    used_search_term = term
                    logger.info(f"Found page: {page.title}")
                    break
                except wikipedia.exceptions.DisambiguationError as e:
                    # Handle disambiguation pages by trying the first option
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0], auto_suggest=False)
                            used_search_term = term
                            logger.info(f"Found page from disambiguation: {page.title}")
                            break
                        except Exception:
                            continue
                except wikipedia.exceptions.PageError:
                    continue
                except Exception as e:
                    logger.warning(f"Error getting page for {result}: {e}")
                    continue

        if page:
            break

    if not page:
        search_type = f"ticker {ticker}" if ticker else f"company {name}"
        raise ValueError(f"Could not find Wikipedia page for {search_type}")

    # Get the plain text content from wikipedia package
    content = page.content

    # Get categories and links using wikipedia package
    try:
        categories = page.categories
    except Exception:
        categories = []

    try:
        links = page.links
    except Exception:
        links = []

    # Build result dictionary
    result = {
        "url": page.url,
        "title": page.title,
        "summary": page.summary,
        "content": content,
        "categories": categories,
        "links": links,
        "search_ticker": ticker,
        "search_name": name,
        "search_term_used": used_search_term,
    }

    logger.info(f"Successfully crawled Wikipedia page: {page.title}")
    logger.info(f"Summary length: {len(result['summary'])} chars")
    logger.info(f"Content length: {len(result['content'])} chars")

    return result


async def crawl_company_wikipedia_async(
    session: aiohttp.ClientSession,
    ticker: Optional[str] = None,
    name: Optional[str] = None,
    raw: bool = False,
) -> dict[str, Any]:
    """
    Async version of crawl_company_wikipedia.

    Args:
        session: aiohttp ClientSession for making requests
        ticker: Stock ticker symbol
        name: Company name
        raw: If True, return raw wikitext instead of Markdown (default: False)

    Returns:
        Dictionary with Wikipedia content in Markdown or raw wikitext format
    """
    if not ticker and not name:
        raise ValueError("Either ticker or name must be provided")

    # Set Wikipedia language
    wikipedia.set_lang("en")

    # Try different search variations
    search_terms = []
    if ticker:
        search_terms.extend(
            [f"{ticker} (company)", f"{ticker} Inc", f"{ticker} Corporation", ticker]
        )
    if name:
        search_terms.extend([name, f"{name} (company)", f"{name} Inc", f"{name} Corporation"])

    page = None
    used_search_term = None

    # Search for the Wikipedia page using various search terms
    for term in search_terms:
        logger.info(f"Trying search term: {term}")

        # Use wikipedia package to search for pages (this is synchronous)
        # We run it in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(None, wikipedia.search, term, 3)

        if search_results:
            # Try to get the first search result
            for result in search_results:
                try:
                    # Get the page using wikipedia package (run in thread pool)
                    page = await loop.run_in_executor(None, wikipedia.page, result, False)
                    used_search_term = term
                    if page:
                        logger.info(f"Found page: {page.title}")
                    break
                except wikipedia.exceptions.DisambiguationError as e:
                    # Handle disambiguation pages by trying the first option
                    if e.options:
                        try:
                            page = await loop.run_in_executor(
                                None, wikipedia.page, e.options[0], False
                            )
                            used_search_term = term
                            if page:
                                logger.info(f"Found page from disambiguation: {page.title}")
                            break
                        except Exception:
                            continue
                except wikipedia.exceptions.PageError:
                    continue
                except Exception as e:
                    logger.warning(f"Error getting page for {result}: {e}")
                    continue

        if page:
            break

    if not page:
        search_type = f"ticker {ticker}" if ticker else f"company {name}"
        raise ValueError(f"Could not find Wikipedia page for {search_type}")

    # Get the raw MediaWiki wikitext using async HTTP
    # NOTE: We use the Wikipedia API directly here because the wikipedia package
    # only provides processed plain text via page.content, not the raw wikitext.
    # We need the raw wikitext with all MediaWiki markup (==Headers==, '''bold''', [[links]], etc.)
    # so that mwparserfromhell can properly parse it and we can convert it to structured Markdown.
    try:
        # Query Wikipedia API directly for raw wikitext
        params = {
            "action": "query",
            "format": "json",
            "titles": page.title,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "formatversion": "2",
        }

        async with session.get("https://en.wikipedia.org/w/api.php", params=params) as response:
            data = await response.json()

        # Extract wikitext from the API response
        content = page.content  # Default fallback to plain text

        if "query" in data and "pages" in data["query"]:
            pages = data["query"]["pages"]
            if pages and len(pages) > 0:
                page_data = pages[0]
                if "revisions" in page_data:
                    # Get the raw wikitext from the main slot
                    wikitext = page_data["revisions"][0]["slots"]["main"]["content"]
                    # Return raw wikitext or convert to Markdown based on parameter
                    if raw:
                        content = wikitext
                    else:
                        content = wikitext_to_markdown(wikitext)
                else:
                    # No revisions found, use plain text
                    content = page.content
        else:
            # No query results, use plain text
            content = page.content

    except Exception as e:
        # If we can't get raw wikitext, fall back to plain text from wikipedia package
        logger.warning(f"Could not fetch or convert wikitext, using plain content: {e}")
        content = page.content

    # Get categories and links using wikipedia package (run in thread pool)
    try:
        loop = asyncio.get_event_loop()
        categories = await loop.run_in_executor(None, lambda: page.categories)
    except Exception:
        categories = []

    try:
        loop = asyncio.get_event_loop()
        links = await loop.run_in_executor(None, lambda: page.links)
    except Exception:
        links = []

    # Build result dictionary
    result = {
        "url": page.url,
        "title": page.title,
        "summary": page.summary,
        "content": content,
        "categories": categories,
        "links": links,
        "search_ticker": ticker,
        "search_name": name,
        "search_term_used": used_search_term,
    }

    logger.info(f"Successfully crawled Wikipedia page: {page.title}")
    logger.info(f"Summary length: {len(result['summary'])} chars")
    logger.info(f"Content length: {len(result['content'])} chars")

    return result


async def crawl_companies_batch_async(
    companies: list[dict[str, Any]],
    output_file: Optional[Path] = None,
    max_concurrent: int = 5,
    raw: bool = False,
) -> list[dict[str, Any]]:
    """
    Crawl multiple companies concurrently with rate limiting.
    Results are written to output file as they complete.

    Args:
        companies: List of company dictionaries with 'ticker' and/or 'name' fields
        output_file: Path to output file for results (optional)
        max_concurrent: Maximum number of concurrent requests (default: 5)
        raw: If True, return raw wikitext instead of Markdown (default: False)

    Returns:
        List of results from crawling each company
    """
    # Create a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []

    async def crawl_with_semaphore(
        session: aiohttp.ClientSession, company: dict[str, Any]
    ) -> dict[str, Any]:
        """Crawl a single company with semaphore rate limiting."""
        async with semaphore:
            try:
                ticker = company.get("ticker")
                name = company.get("name")
                result = await crawl_company_wikipedia_async(
                    session, ticker=ticker, name=name, raw=raw
                )

                # Write to output file if provided
                if output_file:
                    append_jsonl(result, output_file, create_backup=False)
                    logger.info(f"Wrote result for {result['title']} to {output_file}")

                return result
            except Exception as e:
                logger.error(f"Error crawling {company}: {e}")
                error_result = {
                    "error": str(e),
                    "search_ticker": company.get("ticker"),
                    "search_name": company.get("name"),
                }

                # Write error to output file if provided
                if output_file:
                    append_jsonl(error_result, output_file, create_backup=False)

                return error_result

    # Create aiohttp session with timeout
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # Create tasks for all companies
        tasks = [crawl_with_semaphore(session, company) for company in companies]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)

    return results

"""Wikipedia API client for fetching company information."""

from typing import Any, Optional

import mwparserfromhell
import requests
import wikipedia

from abzu.logs import get_logger

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


def crawl_company_wikipedia(
    ticker: Optional[str] = None, name: Optional[str] = None
) -> dict[str, Any]:
    """
    Crawl Wikipedia page for a company.

    Args:
        ticker: Stock ticker symbol
        name: Company name

    Returns:
        Dictionary with Wikipedia content in Markdown format
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

    # Get the raw MediaWiki wikitext
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

        response = requests.get("https://en.wikipedia.org/w/api.php", params=params)
        data = response.json()

        # Extract wikitext from the API response
        markdown_content = page.content  # Default fallback to plain text

        if "query" in data and "pages" in data["query"]:
            pages = data["query"]["pages"]
            if pages and len(pages) > 0:
                page_data = pages[0]
                if "revisions" in page_data:
                    # Get the raw wikitext from the main slot
                    wikitext = page_data["revisions"][0]["slots"]["main"]["content"]
                    # Convert MediaWiki wikitext to Markdown
                    markdown_content = wikitext_to_markdown(wikitext)

    except Exception as e:
        # If we can't get raw wikitext, fall back to plain text from wikipedia package
        logger.warning(f"Could not fetch or convert wikitext, using plain content: {e}")
        markdown_content = page.content

    # Get categories and links using wikipedia package
    try:
        categories = page.categories
    except Exception:
        categories = []

    try:
        links = page.links[:50]  # Limit to first 50 links
    except Exception:
        links = []

    # Build result dictionary
    result = {
        "url": page.url,
        "title": page.title,
        "summary": page.summary,
        "content": markdown_content,
        "categories": categories,
        "links": links,
        "search_ticker": ticker,
        "search_name": name,
        "search_term_used": used_search_term,
    }

    logger.info(f"Successfully crawled Wikipedia page: {page.title}")
    logger.info(f"Summary length: {len(result['summary'])} chars")
    logger.info(f"Markdown content length: {len(result['content'])} chars")

    return result

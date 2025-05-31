"""HTML text extraction utilities."""

import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLExtractor:
    """Extract text content from HTML documents."""

    def __init__(self):
        """Initialize the HTML extractor."""
        pass

    def extract(self, html_content: str) -> str:
        """Extract text content from HTML, preserving structure.

        If the input is plaintext (no HTML tags), returns it unchanged.

        Args:
            html_content: Raw HTML content or plaintext

        Returns:
            Extracted text content with basic formatting preserved
        """
        try:
            if not html_content:
                return ""

            soup = BeautifulSoup(html_content, "html.parser")

            # Check if this is plaintext by looking for any HTML tags
            # beyond the minimal wrapper that BeautifulSoup creates
            all_tags = [tag.name for tag in soup.find_all()]
            # Remove the wrapper tags that BeautifulSoup adds
            meaningful_tags = [tag for tag in all_tags if tag not in ["html", "body", "p"]]

            # If no meaningful HTML tags found, treat as plaintext
            if not meaningful_tags:
                # Check if the body has any direct text that matches our input
                body_text = soup.get_text(strip=True)
                if body_text and body_text.strip() == html_content.strip():
                    return html_content

            # Continue with HTML extraction if we have actual HTML

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get title if available
            title = ""
            if soup.title:
                title = soup.title.string or ""

            # Extract main content
            # Try to find article content in common containers
            article_content = None
            for selector in ["article", "main", "[role='main']", ".content", "#content"]:
                article_content = soup.select_one(selector)
                if article_content:
                    break

            # If no specific container found, use body
            if not article_content:
                article_content = soup.body or soup

            # Extract text with some structure
            lines = []

            # Add title if found
            if title:
                lines.append(f"Title: {title}")
                lines.append("")

            # Process content
            for element in article_content.find_all(
                ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]
            ):
                text = element.get_text(strip=True)
                if text:
                    # Add proper markdown structure markers
                    if element.name == "h1":
                        lines.append("")
                        lines.append(f"# {text}")
                        lines.append("")
                    elif element.name == "h2":
                        lines.append("")
                        lines.append(f"## {text}")
                        lines.append("")
                    elif element.name == "h3":
                        lines.append("")
                        lines.append(f"### {text}")
                        lines.append("")
                    elif element.name == "h4":
                        lines.append("")
                        lines.append(f"#### {text}")
                        lines.append("")
                    elif element.name == "h5":
                        lines.append("")
                        lines.append(f"##### {text}")
                        lines.append("")
                    elif element.name == "h6":
                        lines.append("")
                        lines.append(f"###### {text}")
                        lines.append("")
                    elif element.name == "li":
                        lines.append(f"- {text}")
                    else:
                        lines.append(text)

            # Join lines and clean up excessive whitespace
            text = "\n".join(lines)
            # Remove multiple consecutive blank lines
            while "\n\n\n" in text:
                text = text.replace("\n\n\n", "\n\n")

            return text.strip()

        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            # Fallback: simple text extraction
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator="\n", strip=True)

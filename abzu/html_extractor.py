"""HTML text extraction utilities."""

from bs4 import BeautifulSoup

from abzu.logs import get_logger

logger = get_logger(__name__)


class HTMLExtractor:
    """Extract text content from HTML documents."""

    def __init__(self):
        """Initialize the HTML extractor."""
        pass

    def _log_efficiency(
        self, html_content: str, extracted_text: str, fallback: bool = False
    ) -> None:
        """Log extraction efficiency metrics.

        Args:
            html_content: Original HTML content
            extracted_text: Extracted text content
            fallback: Whether this was a fallback extraction
        """
        original_size = len(html_content)
        extracted_size = len(extracted_text)
        reduction_pct = (
            ((original_size - extracted_size) / original_size * 100) if original_size > 0 else 0
        )
        method = " (fallback)" if fallback else ""
        logger.info(
            f"Extracted text from HTML{method}: {original_size:,} → {extracted_size:,} chars "
            f"({reduction_pct:.1f}% reduction)"
        )

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

            # Initialize the output text variable
            text: str

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

            extracted_text = text.strip()
            self._log_efficiency(html_content, extracted_text)
            return extracted_text

        except Exception as e:
            logger.warning(f"Failed to parse HTML on first pass: {e}")
            # Fallback: simple text extraction
            soup = BeautifulSoup(html_content, "html.parser")
            extracted_text = soup.get_text(separator="\n", strip=True)
            self._log_efficiency(html_content, extracted_text, fallback=True)
            return extracted_text

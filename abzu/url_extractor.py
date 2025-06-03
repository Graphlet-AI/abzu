"""URL extraction and filtering utility."""

import logging
import re
from typing import List, Set
from urllib.parse import urlparse

from lxml import html as lxml_html

from abzu.config import config

logger = logging.getLogger(__name__)


class URLExtractor:
    """Extract and filter URLs from HTML content."""

    def __init__(self, ignore_domains: list[str] = [], replace: bool = False):
        """
        Initialize with ignore list from config and/or provided list.

        Parameters
        ----------
        ignore_domains : list[str]
            Additional domains to ignore
        replace : bool
            If True, replace config domains with provided list.
            If False (default), add provided domains to config list.
        """
        if replace:
            self.ignore_domains = ignore_domains
        else:
            # Get domains from config and add any provided domains
            config_domains = config.get("crawl.ignore", [])
            self.ignore_domains = list(set(config_domains + ignore_domains))

        # Remove empty strings from ignore list
        self.ignore_domains = [d for d in self.ignore_domains if d]
        logger.info(f"URLExtractor initialized with ignore domains: {self.ignore_domains}")

    def should_ignore_url(self, url: str) -> bool:
        """
        Check if a URL should be ignored based on the ignore list.

        Parameters
        ----------
        url : str
            The URL to check

        Returns
        -------
        bool
            True if the URL should be ignored, False otherwise
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return False

            # Check if hostname exactly matches or is a subdomain of any ignored domain
            for domain in self.ignore_domains:
                if hostname == domain or hostname.endswith(f".{domain}"):
                    logger.debug(f"URL ignored due to domain '{domain}': {url}")
                    return True

            return False

        except Exception as e:
            logger.warning(f"Failed to parse URL '{url}': {e}")
            return False

    def extract_urls_from_html(self, html: str) -> List[str]:
        """
        Extract all URLs from HTML content and filter out ignored domains.

        Parameters
        ----------
        html : str
            HTML content to extract URLs from

        Returns
        -------
        List[str]
            List of URLs that are not in the ignore list
        """
        try:
            # Parse HTML using lxml
            tree = lxml_html.fromstring(html)
        except Exception as e:
            logger.warning(f"Failed to parse HTML: {e}")
            return []

        urls: Set[str] = set()

        # Extract URLs from href attributes
        for element in tree.xpath("//*[@href]"):
            url = element.get("href", "").strip()
            if url:
                urls.add(url)

        # Extract URLs from src attributes
        for element in tree.xpath("//*[@src]"):
            url = element.get("src", "").strip()
            if url:
                urls.add(url)

        # Also extract plain text URLs using lxml's text_content()
        text_content = tree.text_content()
        # Find URLs in plain text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\']+'
        text_urls = re.findall(url_pattern, text_content)
        urls.update(text_urls)

        # Filter URLs
        filtered_urls = []
        ignored_count = 0

        for url in urls:
            # Skip relative URLs, anchors, and javascript
            if url.startswith(("http://", "https://")) and not url.startswith(
                ("javascript:", "mailto:", "#")
            ):

                if not self.should_ignore_url(url):
                    filtered_urls.append(url)
                else:
                    ignored_count += 1

        if ignored_count > 0:
            logger.info(f"Filtered out {ignored_count} URLs from ignored domains")

        logger.debug(f"Extracted {len(filtered_urls)} URLs after filtering")
        return sorted(filtered_urls)  # Sort for consistent output

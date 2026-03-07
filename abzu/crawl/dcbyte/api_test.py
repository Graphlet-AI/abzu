"""Test direct API calls to DC Byte blog's Essential Grid endpoint."""

import json
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from abzu.logs import get_logger

logger = get_logger(__name__)


class DCByteAPIClient:
    """Client for interacting with DC Byte blog's Essential Grid API."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "en-US,en;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://www.dcbyte.com/us/news-blogs/",
                "Origin": "https://www.dcbyte.com",
            }
        )
        self.base_url = "https://www.dcbyte.com"
        self.ajax_url = f"{self.base_url}/wp-admin/admin-ajax.php"
        self.blog_url = f"{self.base_url}/us/news-blogs/"
        self.token: str | None = None
        self.gridid: str | None = None
        self.loaded_post_ids: list[str] = []

    def get_initial_page(self) -> tuple[str | None, str | None, list[dict[str, Any]]]:
        """Get the initial blog page and extract Essential Grid configuration."""
        try:
            response = self.session.get(self.blog_url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract token from the page
            token_match = re.search(r'token["\']?\s*:\s*["\']([a-zA-Z0-9]+)["\']', response.text)
            if token_match:
                self.token = token_match.group(1)
                logger.info(f"Found token: {self.token}")

            # Extract grid ID
            grid_match = re.search(r'gridid["\']?\s*:\s*["\']?(\d+)["\']?', response.text)
            if not grid_match:
                # Try alternative patterns
                grid_match = re.search(r'data-gridid=["\'](\d+)["\']', response.text)
                if not grid_match:
                    grid_match = re.search(r"eg-[\w-]+-(\d+)", response.text)

            if grid_match:
                self.gridid = grid_match.group(1)
                logger.info(f"Found grid ID: {self.gridid}")

            # Extract initial post IDs from the page
            posts = []
            # Look for Essential Grid items
            grid_items = soup.find_all(["article", "li"], class_=re.compile(r"eg-.*-element"))

            for item in grid_items:
                post_data = {}

                # Try to extract post ID
                post_id = item.get("data-post-id") or item.get("id", "").replace("post-", "")
                if post_id:
                    post_data["id"] = post_id
                    self.loaded_post_ids.append(post_id)

                # Extract title
                title_elem = item.find(["h2", "h3", "h4"], class_=re.compile(r"eg-.*-element"))
                if title_elem:
                    post_data["title"] = title_elem.get_text(strip=True)

                # Extract link
                link_elem = item.find("a", href=True)
                if link_elem:
                    post_data["url"] = link_elem["href"]

                # Extract date
                date_elem = item.find(class_=re.compile(r"(date|meta|time)"))
                if date_elem:
                    post_data["date"] = date_elem.get_text(strip=True)

                if post_data:
                    posts.append(post_data)

            logger.info(f"Found {len(posts)} initial posts")
            logger.info(f"Loaded post IDs: {self.loaded_post_ids}")

            return self.token, self.gridid, posts

        except Exception as e:
            logger.error(f"Error fetching initial page: {e}")
            return None, None, []

    def load_more_posts(self, page: int = 1) -> list[dict[str, Any]]:
        """Load more posts using the Essential Grid AJAX endpoint."""
        if not self.token or not self.gridid:
            logger.error("Token or grid ID not found. Run get_initial_page() first.")
            return []

        try:
            # Prepare the data for the AJAX request
            data = {
                "action": "Essential_Grid_Front_request_ajax",
                "client_action": "load_more_items",
                "token": self.token,
                "gridid": self.gridid,
            }

            # Add loaded post IDs
            for post_id in self.loaded_post_ids:
                data["data[]"] = post_id

            logger.info("Making AJAX request with data: %s", data)

            response = self.session.post(self.ajax_url, data=data)
            response.raise_for_status()

            # Try to parse JSON response
            try:
                result = response.json()
                logger.info(f"JSON Response: {json.dumps(result, indent=2)[:500]}...")

                # Extract posts from the response
                posts = []
                if isinstance(result, dict):
                    # The response might contain HTML in a 'data' or 'content' field
                    html_content = result.get("data") or result.get("content") or ""
                    if html_content:
                        posts = self.parse_posts_from_html(html_content)

                    # Update loaded post IDs if provided
                    if "post_ids" in result:
                        self.loaded_post_ids.extend(result["post_ids"])

                return posts

            except json.JSONDecodeError:
                # Response might be HTML directly
                logger.info("Response is not JSON, parsing as HTML")
                return self.parse_posts_from_html(response.text)

        except Exception as e:
            logger.error(f"Error loading more posts: {e}")
            return []

    def parse_posts_from_html(self, html: str) -> list[dict[str, Any]]:
        """Parse posts from HTML content."""
        posts = []
        soup = BeautifulSoup(html, "html.parser")

        # Look for article elements or grid items
        items = soup.find_all(["article", "li", "div"], class_=re.compile(r"(eg-|post|blog)"))

        for item in items:
            post_data = {}

            # Extract title
            title_elem = item.find(["h1", "h2", "h3", "h4", "a"])
            if title_elem:
                post_data["title"] = title_elem.get_text(strip=True)

            # Extract link
            link_elem = item.find("a", href=True)
            if link_elem:
                post_data["url"] = link_elem["href"]
                if not post_data["url"].startswith("http"):
                    post_data["url"] = self.base_url + post_data["url"]

            # Extract excerpt
            excerpt_elem = item.find(["p", "div"], class_=re.compile(r"(excerpt|summary|content)"))
            if excerpt_elem:
                post_data["excerpt"] = excerpt_elem.get_text(strip=True)

            # Extract date
            date_elem = item.find(class_=re.compile(r"(date|meta|time)"))
            if date_elem:
                post_data["date"] = date_elem.get_text(strip=True)

            if post_data and "url" in post_data:
                posts.append(post_data)
                # Extract post ID from URL if possible
                id_match = re.search(r"/(\d+)/$", post_data["url"])
                if id_match:
                    self.loaded_post_ids.append(id_match.group(1))

        logger.info(f"Parsed {len(posts)} posts from HTML")
        return posts


def main() -> None:
    """Test the DC Byte API client."""
    client: DCByteAPIClient = DCByteAPIClient()

    # Get initial page and configuration
    logger.info("=" * 80)
    logger.info("FETCHING INITIAL PAGE")
    logger.info("=" * 80)

    token, gridid, initial_posts = client.get_initial_page()

    if token and gridid:
        logger.info("✓ Successfully extracted configuration")
        logger.info(f"  Token: {token}")
        logger.info(f"  Grid ID: {gridid}")
        logger.info(f"  Initial posts: {len(initial_posts)}")

        if initial_posts:
            logger.info("\nSample initial posts:")
            for post in initial_posts[:3]:
                logger.info(f"  - {post}")

        # Try to load more posts
        logger.info("\n" + "=" * 80)
        logger.info("LOADING MORE POSTS")
        logger.info("=" * 80)

        more_posts = client.load_more_posts()

        if more_posts:
            logger.info(f"✓ Successfully loaded {len(more_posts)} more posts")
            logger.info("\nSample loaded posts:")
            for post in more_posts[:3]:
                logger.info(f"  - {post}")
        else:
            logger.warning("✗ Could not load more posts via API")
            logger.info("\nRecommendation: Use Playwright for browser-based scraping")
    else:
        logger.error("✗ Could not extract Essential Grid configuration")
        logger.info("\nRecommendation: Use Playwright for browser-based scraping")

    # Save results
    results = {
        "token_found": token is not None,
        "gridid_found": gridid is not None,
        "initial_posts_count": len(initial_posts),
        "can_use_api": token is not None and gridid is not None,
        "recommendation": "Use API calls" if (token and gridid) else "Use Playwright",
    }

    with open("dcbyte_api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("\n" + "=" * 80)
    logger.info("FINAL RECOMMENDATION")
    logger.info("=" * 80)
    logger.info(results["recommendation"])


if __name__ == "__main__":
    main()

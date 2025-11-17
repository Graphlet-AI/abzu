"""Unit tests for URLExtractor."""

from unittest.mock import patch

import pytest

from abzu.url_extractor import URLExtractor


@pytest.fixture
def mock_config():
    """Mock config with test ignore domains."""
    with patch("abzu.url_extractor.config") as mock:
        mock.get.return_value = ["example.com", "test.org"]
        yield mock


def test_init_with_config_domains(mock_config):
    """Test initialization with domains from config."""
    extractor = URLExtractor()
    assert set(extractor.ignore_domains) == {"example.com", "test.org"}


def test_init_with_additional_domains(mock_config):
    """Test initialization with additional domains."""
    extractor = URLExtractor(ignore_domains=["extra.net"])
    assert set(extractor.ignore_domains) == {"example.com", "test.org", "extra.net"}


def test_init_with_replace_true(mock_config):
    """Test initialization with replace=True ignores config."""
    extractor = URLExtractor(ignore_domains=["only.com"], replace=True)
    assert extractor.ignore_domains == ["only.com"]
    # Verify config was accessed but not used
    mock_config.get.assert_not_called()


def test_init_removes_empty_strings(mock_config):
    """Test that empty strings are removed from ignore list."""
    mock_config.get.return_value = ["example.com", "", "test.org", ""]
    extractor = URLExtractor(ignore_domains=["", "extra.net"])
    assert "" not in extractor.ignore_domains
    assert set(extractor.ignore_domains) == {"example.com", "test.org", "extra.net"}


def test_should_ignore_url_exact_match():
    """Test URL filtering with exact domain match."""
    extractor = URLExtractor(ignore_domains=["example.com"], replace=True)

    assert extractor.should_ignore_url("https://example.com/page")
    assert extractor.should_ignore_url("http://example.com/page")
    assert not extractor.should_ignore_url("https://other.com/page")


def test_should_ignore_url_subdomain():
    """Test URL filtering with subdomains."""
    extractor = URLExtractor(ignore_domains=["example.com"], replace=True)

    assert extractor.should_ignore_url("https://www.example.com/page")
    assert extractor.should_ignore_url("https://api.example.com/page")
    assert extractor.should_ignore_url("https://deep.sub.example.com/page")
    assert not extractor.should_ignore_url("https://example.net/page")


def test_should_ignore_url_invalid_urls():
    """Test URL filtering with invalid URLs."""
    extractor = URLExtractor(ignore_domains=["example.com"], replace=True)

    # Invalid URLs should not be ignored (return False)
    assert not extractor.should_ignore_url("not-a-url")
    assert not extractor.should_ignore_url("")

    # Protocol-relative URLs with matching domain should be ignored
    # (urlparse treats //example.com as having hostname example.com)
    assert extractor.should_ignore_url("//example.com")

    # FTP URLs with matching domain should still be ignored
    assert extractor.should_ignore_url("ftp://example.com")


def test_extract_urls_from_html_basic():
    """Test basic URL extraction from HTML."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <a href="https://example.com/page1">Link 1</a>
        <a href="https://test.org/page2">Link 2</a>
        <img src="https://cdn.example.com/image.jpg">
        <p>Check out https://inline.com/resource for more info</p>
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 4
    assert "https://example.com/page1" in urls
    assert "https://test.org/page2" in urls
    assert "https://cdn.example.com/image.jpg" in urls
    assert "https://inline.com/resource" in urls


def test_extract_urls_from_html_with_filtering():
    """Test URL extraction with domain filtering."""
    extractor = URLExtractor(ignore_domains=["example.com"], replace=True)

    html = """
    <html>
        <a href="https://example.com/page1">Ignored</a>
        <a href="https://www.example.com/page2">Also Ignored</a>
        <a href="https://test.org/page3">Kept</a>
        <a href="https://keepme.com/page4">Also Kept</a>
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 2
    assert "https://test.org/page3" in urls
    assert "https://keepme.com/page4" in urls
    assert "https://example.com/page1" not in urls
    assert "https://www.example.com/page2" not in urls


def test_extract_urls_skips_relative_and_special():
    """Test that relative URLs and special schemes are skipped."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <a href="/relative/path">Relative</a>
        <a href="javascript:void(0)">JavaScript</a>
        <a href="mailto:test@example.com">Email</a>
        <a href="#anchor">Anchor</a>
        <a href="https://valid.com/page">Valid</a>
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 1
    assert urls[0] == "https://valid.com/page"


def test_extract_urls_deduplicates():
    """Test that duplicate URLs are removed."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <a href="https://example.com/page">Link 1</a>
        <a href="https://example.com/page">Link 2</a>
        <img src="https://example.com/page">
        <p>Also see https://example.com/page</p>
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 1
    assert urls[0] == "https://example.com/page"


def test_extract_urls_sorted_output():
    """Test that URLs are returned in sorted order."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <a href="https://zebra.com">Z</a>
        <a href="https://alpha.com">A</a>
        <a href="https://middle.com">M</a>
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert urls == ["https://alpha.com", "https://middle.com", "https://zebra.com"]


def test_extract_urls_handles_quotes():
    """Test URL extraction handles both single and double quotes."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <a href="https://double.com">Double</a>
        <a href='https://single.com'>Single</a>
        <img src="https://img1.com" />
        <img src='https://img2.com' />
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 4
    assert all(
        url in urls
        for url in [
            "https://double.com",
            "https://single.com",
            "https://img1.com",
            "https://img2.com",
        ]
    )


def test_extract_urls_case_insensitive():
    """Test that URL extraction is case-insensitive for tags."""
    extractor = URLExtractor(ignore_domains=[], replace=True)

    html = """
    <html>
        <A HREF="https://upper.com">Upper</A>
        <a HrEf="https://mixed.com">Mixed</a>
        <IMG SRC="https://imgupper.com">
    </html>
    """

    urls = extractor.extract_urls_from_html(html)
    assert len(urls) == 3
    assert all(
        url in urls for url in ["https://upper.com", "https://mixed.com", "https://imgupper.com"]
    )

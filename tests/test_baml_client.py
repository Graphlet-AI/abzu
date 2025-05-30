"""Integration tests for abzu.baml_client ExtractIndustryArticle function."""

import pytest

from abzu.baml_client import b
from abzu.baml_client.types import IndustryArticle


@pytest.fixture
def sample_article_html():
    """Load sample article HTML from tests/article.py."""

    with open("tests/article.html", "r") as f:
        html = f.read()

    return html


def test_extract_industry_article_sync_real(sample_article_html):
    """Test sync extraction of industry article from HTML using real LLM."""
    # Call the real BAML client
    result = b.ExtractIndustryArticle(sample_article_html)

    # Verify the result structure
    assert isinstance(result, IndustryArticle)
    assert result.title is not None and len(result.title) > 0
    assert result.summary is not None and len(result.summary) > 0

    # The article should extract AMD and NVIDIA as companies
    assert result.companies is not None
    company_names = [c.name for c in result.companies]
    assert "AMD" in company_names
    assert "NVIDIA" in company_names

    # Should extract GPU products
    assert result.products is not None
    product_names = [p.name for p in result.products]
    assert any("MI300X" in p for p in product_names)
    assert any("H100" in p or "H200" in p for p in product_names)

    # Should extract technologies
    assert result.technologies is not None
    tech_names = [t.name for t in result.technologies]
    assert any("vLLM" in t or "VLLM" in t for t in tech_names)


def test_extract_empty_html_real():
    """Test extraction with empty HTML using real LLM."""
    # Empty input might raise an error or return minimal content
    try:
        result = b.ExtractIndustryArticle("")
        # If it succeeds, check basic structure
        assert isinstance(result, IndustryArticle)
        assert result.title is not None
        assert result.summary is not None
    except Exception as e:
        # This is expected for empty input
        # The error message should indicate validation or parsing issue
        assert (
            "validation" in str(e).lower() or "parse" in str(e).lower() or "empty" in str(e).lower()
        )


def test_extract_minimal_html_real():
    """Test extraction with minimal HTML content using real LLM."""
    minimal_html = """
    <html>
    <body>
        <h1>AMD Announces New MI400X GPU</h1>
        <p>AMD today revealed their latest MI400X GPU for AI workloads,
        competing directly with NVIDIA's H200.</p>
    </body>
    </html>
    """

    result = b.ExtractIndustryArticle(minimal_html)

    assert isinstance(result, IndustryArticle)
    assert "MI400X" in result.title or "MI400X" in result.summary

    # Should extract AMD as a company
    if result.companies:
        company_names = [c.name for c in result.companies]
        assert "AMD" in company_names


def test_model_dump_serialization_real(sample_article_html):
    """Test that the IndustryArticle model can be serialized after real extraction."""
    result = b.ExtractIndustryArticle(sample_article_html)

    # Test model_dump functionality
    dumped = result.model_dump()

    assert isinstance(dumped, dict)
    assert "title" in dumped
    assert "summary" in dumped
    assert dumped["title"] == result.title

    # Check nested structures are properly serialized
    if result.companies:
        assert isinstance(dumped["companies"], list)
        assert isinstance(dumped["companies"][0], dict)
        assert "name" in dumped["companies"][0]
        assert "description" in dumped["companies"][0]


def test_extract_article_partnerships_real(sample_article_html):
    """Test that partnerships are extracted from the article."""
    result = b.ExtractIndustryArticle(sample_article_html)

    # The article mentions partnerships like NVIDIA-SGLang
    if result.partnerships:
        partnership_descriptions = [
            p.description for p in result.partnerships if p.description is not None
        ]
        # At least one partnership should be found
        assert len(partnership_descriptions) > 0


def test_extract_article_tickers_real(sample_article_html):
    """Test that stock tickers are extracted."""
    result = b.ExtractIndustryArticle(sample_article_html)

    if result.tickers:
        ticker_symbols = [t.symbol for t in result.tickers]
        # AMD and NVDA are likely ticker symbols
        assert any(t in ticker_symbols for t in ["AMD", "NVDA", "NVIDIA"])


def test_extract_html_with_special_characters_real():
    """Test extraction from HTML with special characters and entities."""
    special_html = """
    <html>
    <body>
        <h1>Tech &amp; Innovation: AMD's $1B M&amp;A Deal</h1>
        <p>AMD &gt; NVIDIA in certain benchmarks &lt; 100ms latency</p>
        <p>Partnership between AT&amp;T and Verizon &amp; T-Mobile.</p>
    </body>
    </html>
    """

    result = b.ExtractIndustryArticle(special_html)

    assert isinstance(result, IndustryArticle)
    # Check that special characters are handled
    assert result.title is not None
    assert result.summary is not None

    # The content should mention AMD and benchmarks
    content = f"{result.title} {result.summary}".lower()
    assert "amd" in content

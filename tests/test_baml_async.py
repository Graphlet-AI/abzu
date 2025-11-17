"""Quick async test for BAML client."""

import pytest

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.types import IndustryArticle


@pytest.fixture
def sample_article_html():
    """Load sample article HTML from tests/article.py."""

    with open("tests/article.html", "r") as f:
        html = f.read()

    return html


@pytest.mark.asyncio
async def test_extract_simple_article_async():
    """Test async extraction with a simple article."""
    test_html = """
    <html>
    <body>
        <h1>AMD Beats NVIDIA in AI Benchmarks</h1>
        <p>AMD's new MI350X GPU shows 25% better performance than NVIDIA's H200
        in large language model inference tasks.</p>
    </body>
    </html>
    """

    result = await async_b.ExtractIndustryArticle(test_html)

    # Verify the result
    assert isinstance(result, IndustryArticle)
    assert result.title is not None
    assert "AMD" in result.title or "AMD" in result.summary
    assert result.companies is not None
    assert len(result.companies) >= 2  # Should have at least AMD and NVIDIA

    # Check company names
    company_names = [c.name for c in result.companies]
    # Check that AMD and NVIDIA are mentioned (may be full names)
    assert any("AMD" in name or "Advanced Micro Devices" in name for name in company_names)
    assert any("NVIDIA" in name for name in company_names)


@pytest.mark.asyncio
async def test_extract_article_with_deals_real(sample_article_html):
    """Test that deals are extracted correctly from the article."""
    result = await async_b.ExtractIndustryArticle(sample_article_html)

    # The article mentions AMD's $749 million stock buyback
    if result.deals:
        # Check if any deal mentions the buyback
        buyback_deals = [
            d for d in result.deals if "buyback" in d.description.lower() or "749" in d.description
        ]
        assert len(buyback_deals) > 0 or any(
            "AMD" in d.src_company.name for d in result.deals if d.src_company
        )


@pytest.mark.asyncio
async def test_performance_comparison_content(sample_article_html):
    """Test that the performance comparison content is captured."""
    result = await async_b.ExtractIndustryArticle(sample_article_html)

    # The article is about AMD vs NVIDIA inference performance
    summary_lower = result.summary.lower()
    assert "amd" in summary_lower
    assert "nvidia" in summary_lower
    assert any(
        word in summary_lower for word in ["performance", "inference", "benchmark", "comparison"]
    )


@pytest.mark.asyncio
async def test_cited_sources_extraction(sample_article_html):
    """Test that cited sources are extracted from the article."""
    result = await async_b.ExtractIndustryArticle(sample_article_html)

    # The article cites several sources like SemiAnalysis, Peking University, etc.
    if result.cited_sources:
        source_names = [s.name for s in result.cited_sources]
        # At least SemiAnalysis should be found as it's the main source
        assert any("semianalysis" in s.lower() for s in source_names)


@pytest.mark.asyncio
async def test_extract_industry_article_async_real(sample_article_html):
    """Test async extraction of industry article from HTML using real LLM."""
    # Call the real BAML client
    result = await async_b.ExtractIndustryArticle(sample_article_html)

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

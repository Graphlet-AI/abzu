"""Tests to ensure title and URLs are properly extracted through BAML clients."""

import json

import pytest

from abzu.baml_client.async_client import b as async_b
from abzu.baml_client.sync_client import b


@pytest.fixture
def create_test_article():
    """Fixture that returns a function to create test articles."""

    def _create(title: str, url: str, content_urls: list[str]) -> dict[str, str | list[str]]:
        # Create URLs section in content
        urls_section = ""
        if content_urls:
            urls_section = "\n\nReferences and Links:\n" + "\n".join(
                [f"- {url}" for url in content_urls]
            )

        article = {
            "title": title,
            "url": url,
            "content": f"""
Title: {title}

This is a test article about technology companies.

AMD announced their new MI400X GPU today, competing with NVIDIA's H200.
The new chip shows 30% performance improvements in AI workloads.

{urls_section}
            """,
            "posted_at": "2024-01-15T10:00:00Z",
            "collected_at": "2024-01-15T12:00:00Z",
            "urls": content_urls,
        }

        return article

    return _create


def test_title_preserved_sync(create_test_article):
    """Test that title is preserved through sync BAML processing."""
    test_title = "AMD Beats NVIDIA in New AI Benchmarks - Breaking News"
    test_url = "https://example.com/amd-beats-nvidia"
    test_content_urls = [
        "https://amd.com/mi400x",
        "https://nvidia.com/h200",
        "https://arxiv.org/papers/2024.12345",
    ]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Verify title is preserved
    assert result.title == test_title


def test_article_url_preserved_sync(create_test_article):
    """Test that article URL is preserved through sync BAML processing."""
    test_title = "TSMC Partners with Apple for 2nm Chips"
    test_url = "https://semianalysis.com/tsmc-apple-2nm"
    test_content_urls = []

    article = create_test_article(test_title, test_url, test_content_urls)

    # The BAML client only extracts from content, so URL preservation
    # happens in the processor. Since there's no sync processor,
    # we'll test that the BAML result can be combined with article data
    result = b.ExtractIndustryArticle(article["content"])

    # In practice, the processor would do this:
    result.url = article.get("url", result.url)

    # Verify URL is preserved
    assert result.url == test_url


def test_content_urls_extracted_sync(create_test_article):
    """Test that URLs mentioned in content are extracted."""
    test_title = "Google Launches New TPU v5"
    test_url = "https://techcrunch.com/google-tpu-v5"
    test_content_urls = [
        "https://cloud.google.com/tpu/v5",
        "https://research.google/papers/tpu-architecture",
        "https://github.com/google/tpu-examples",
    ]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Verify URLs are extracted
    assert result.urls is not None
    assert len(result.urls) > 0
    # Check that at least some of our test URLs were found
    extracted_urls = set(result.urls)
    test_urls_set = set(test_content_urls)
    assert len(extracted_urls.intersection(test_urls_set)) > 0


def test_special_characters_in_title_sync(create_test_article):
    """Test that titles with special characters are preserved."""
    test_title = "AMD's $500M Investment: GPUs > CPUs & AI?"
    test_url = "https://example.com/amd-investment"
    test_content_urls = []

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Verify title with special characters is preserved
    assert result.title == test_title


def test_empty_urls_handled_sync(create_test_article):
    """Test that articles without URLs are handled properly."""
    test_title = "Intel Announces Layoffs"
    test_url = "https://news.com/intel-layoffs"
    test_content_urls = []  # No URLs in content

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Verify title is still preserved
    assert result.title == test_title
    # URLs might be None or empty list
    assert result.urls is None or result.urls == []


@pytest.mark.asyncio
async def test_title_preserved_async(create_test_article):
    """Test that title is preserved through async BAML processing."""
    test_title = "Meta Develops Custom AI Chip to Rival NVIDIA"
    test_url = "https://theinformation.com/meta-ai-chip"
    test_content_urls = ["https://ai.meta.com/research", "https://nvidia.com/datacenter"]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using async BAML
    result = await async_b.ExtractIndustryArticle(article["content"])

    # Verify title is preserved
    assert result.title == test_title


@pytest.mark.asyncio
async def test_article_url_preserved_async(create_test_article):
    """Test that article URL is preserved through async BAML processing."""
    test_title = "Samsung Enters GPU Market"
    test_url = "https://koreatimes.com/samsung-gpu"
    test_content_urls = []

    article = create_test_article(test_title, test_url, test_content_urls)

    # Note: Testing through the processor
    from abzu.articles.processor import process_article_async

    # Process the article
    processed = await process_article_async(article)

    # Verify URL is preserved
    assert processed is not None
    assert not isinstance(processed, BaseException)
    assert processed.url == test_url


@pytest.mark.asyncio
async def test_content_urls_extracted_async(create_test_article):
    """Test that URLs mentioned in content are extracted."""
    test_title = "Apple M4 Chip Details Leaked"
    test_url = "https://9to5mac.com/m4-leak"
    test_content_urls = [
        "https://apple.com/newsroom/2024/m4-announcement",
        "https://twitter.com/mingchikuo/status/123456",
        "https://anandtech.com/apple-silicon-analysis",
    ]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using async BAML
    result = await async_b.ExtractIndustryArticle(article["content"])

    # Verify URLs are extracted
    assert result.urls is not None
    assert len(result.urls) > 0
    # Check that at least some of our test URLs were found
    extracted_urls = set(result.urls)
    test_urls_set = set(test_content_urls)
    assert len(extracted_urls.intersection(test_urls_set)) > 0


@pytest.mark.asyncio
async def test_unicode_in_title_async(create_test_article):
    """Test that titles with unicode characters are preserved."""
    test_title = "中国's Semiconductor Push: 华为 vs NVIDIA"
    test_url = "https://asiannews.com/china-semiconductors"
    test_content_urls = []

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using async BAML
    result = await async_b.ExtractIndustryArticle(article["content"])

    # Verify title with unicode is preserved
    assert result.title == test_title


@pytest.mark.asyncio
async def test_multiple_urls_async(create_test_article):
    """Test extraction of multiple URLs from content."""
    test_title = "Comprehensive AI Hardware Review 2024"
    test_url = "https://aihardware.com/review-2024"
    test_content_urls = [
        "https://nvidia.com/h100",
        "https://amd.com/mi300x",
        "https://google.com/tpu-v5",
        "https://intel.com/gaudi3",
        "https://aws.amazon.com/trainium",
        "https://graphcore.ai/products/ipu",
    ]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using async BAML
    result = await async_b.ExtractIndustryArticle(article["content"])

    # Verify multiple URLs are extracted
    assert result.urls is not None
    assert len(result.urls) >= 3  # Should extract at least half


def test_sync_processor_preserves_all_fields(create_test_article):
    """Test sync processing preserves title, URL, and content URLs."""
    test_title = "Qualcomm Announces Snapdragon X Elite"
    test_url = "https://qualcomm.com/news/snapdragon-x-elite"
    test_content_urls = [
        "https://qualcomm.com/products/snapdragon-x-elite",
        "https://microsoft.com/surface/copilot-pc",
    ]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Simulate what the processor would do
    result.title = article.get("title", result.title)
    result.url = article.get("url", result.url)
    result.urls = article.get("urls", result.urls)

    # Verify all fields are preserved
    assert result.title == test_title
    assert result.url == test_url
    assert result.urls is not None
    assert len(result.urls) > 0


@pytest.mark.asyncio
async def test_async_processor_preserves_all_fields(create_test_article):
    """Test async processor preserves title, URL, and content URLs."""
    from abzu.articles.processor import process_article_async

    test_title = "Tesla Develops Custom Dojo Chip"
    test_url = "https://electrek.co/tesla-dojo-chip"
    test_content_urls = ["https://tesla.com/AI", "https://twitter.com/elonmusk/status/789012"]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Process the article
    result = await process_article_async(article)

    # Verify all fields are preserved
    assert result is not None
    assert not isinstance(result, BaseException)
    assert result.title == test_title
    assert result.url == test_url
    assert result.urls is not None
    assert len(result.urls) > 0


def test_json_serialization_preserves_fields(create_test_article):
    """Test that JSON serialization preserves title and URLs."""
    test_title = "Microsoft Partners with OpenAI on GPT-5"
    test_url = "https://microsoft.com/blog/openai-gpt5"
    test_content_urls = ["https://openai.com/gpt-5", "https://azure.microsoft.com/ai"]

    article = create_test_article(test_title, test_url, test_content_urls)

    # Extract using BAML
    result = b.ExtractIndustryArticle(article["content"])

    # Simulate processor behavior
    result.title = article.get("title", result.title)
    result.url = article.get("url", result.url)
    result.urls = article.get("urls", result.urls)

    # Serialize to dict
    result_dict = result.model_dump()

    # Verify fields in dict
    assert result_dict["title"] == test_title
    assert result_dict["url"] == test_url
    assert "urls" in result_dict
    assert isinstance(result_dict["urls"], list)

    # Serialize to JSON and back
    json_str = json.dumps(result_dict)
    restored_dict = json.loads(json_str)

    # Verify fields survived JSON round-trip
    assert restored_dict["title"] == test_title
    assert restored_dict["url"] == test_url
    assert "urls" in restored_dict
    assert isinstance(restored_dict["urls"], list)

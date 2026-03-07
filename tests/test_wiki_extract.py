"""Test extraction of company info from Wikipedia."""

from pathlib import Path

from abzu.api.wiki import extract_company_info


def test_extract_nvidia_info():
    """Test that we can extract all key fields from NVIDIA's Wikipedia page."""
    # Load the downloaded NVIDIA text
    nvidia_file = Path(__file__).parent / "assets" / "nvidia.txt"
    with open(nvidia_file) as f:
        content = f.read()

    # Create page data structure
    page_data = {
        "title": "Nvidia",
        "url": "https://en.wikipedia.org/wiki/Nvidia",
        "summary": "Nvidia Corporation is an American technology company headquartered in Santa Clara, California.",
        "content": content,
    }

    # Extract info
    result = extract_company_info(page_data)

    # Required fields should exist and have values
    assert result["name"] == "Nvidia"

    # Ticker should be extracted
    assert result["ticker"] is not None
    assert result["ticker"]["symbol"] == "NVDA"
    assert result["ticker"]["exchange"] == "NASDAQ"

    # Website URL - may not be in plain text
    # If website_url is found, it should contain nvidia
    if result["website_url"]:
        assert "nvidia" in result["website_url"].lower()

    # Headquarters location
    assert result["headquarters_location"] is not None
    assert "Santa Clara" in result["headquarters_location"]

    # Revenue
    assert result["revenue_usd"] is not None
    assert result["revenue_usd"] > 0

    # Employees - may not be in plain text
    # If employees is found, it should be positive
    if result["employees"]:
        assert result["employees"] > 0

    # Founded year
    assert result["founded_year"] == 1993

    # CEO
    assert result["ceo"] == "Jensen Huang"


def test_extract_company_info_minimal_data():
    """Test extraction with minimal data."""
    content = "Unknown Company is a mysterious organization with limited public information."

    data = {
        "title": "Unknown Company",
        "url": "https://en.wikipedia.org/wiki/Unknown",
        "summary": "A mysterious company.",
        "content": content,
    }

    result = extract_company_info(data, name="Unknown Corp")

    # Verify all fields exist
    assert "name" in result
    assert "ticker" in result
    assert "description" in result
    assert "website_url" in result
    assert "headquarters_location" in result
    assert "revenue_usd" in result
    assert "employees" in result
    assert "founded_year" in result
    assert "ceo" in result
    assert "linkedin_url" in result

    # Verify values for minimal data
    assert result["name"] == "Unknown Company"  # Uses title over provided name
    assert result["ticker"] is None
    assert result["description"] == "A mysterious company."
    assert result["headquarters_location"] is None
    assert result["revenue_usd"] is None
    assert result["employees"] is None
    assert result["founded_year"] is None
    assert result["ceo"] is None
    assert result["website_url"] is None
    assert result["linkedin_url"] is None

#!/usr/bin/env python3
"""Test UUID accumulation and mapping in entity resolution."""

import asyncio
import logging
import uuid as uuid_mod
from unittest.mock import AsyncMock

import pytest

from abzu.er.uuid import process_block_with_uuid_mapping
from abzu.logs import get_logger

logger = get_logger(__name__)


class MockCompany:
    """Mock company object matching BAML response structure."""

    def __init__(self, id: int, source_ids: list[int], **kwargs):
        self.id = id
        self.uuid = str(uuid_mod.uuid4())  # Generate a new UUID for merged company
        self.source_ids = source_ids
        self.name = kwargs.get("name", "Test Company")
        self.cik = kwargs.get("cik")
        self.ticker = kwargs.get("ticker")
        self.description = kwargs.get("description", "")
        self.website_url = kwargs.get("website_url")
        self.headquarters_location = kwargs.get("headquarters_location")
        self.jurisdiction = kwargs.get("jurisdiction")
        self.revenue_usd = kwargs.get("revenue_usd")
        self.employees = kwargs.get("employees")
        self.founded_year = kwargs.get("founded_year")
        self.ceo = kwargs.get("ceo")
        self.linkedin_url = kwargs.get("linkedin_url")


class MockResolvedCompanyList:
    """Mock resolved company list from BAML."""

    def __init__(self, companies: list[MockCompany]):
        self.companies = companies


@pytest.mark.asyncio
async def test_uuid_accumulation_with_existing_source_uuids():
    """
    Test that when companies with existing source_uuids are merged,
    all source_uuids are properly accumulated through the ID mapping process.
    """
    # Create test companies with pre-existing source_uuids
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "Acme Corporation",
            "description": "A company",
            "source_uuids": ["old-uuid-1", "old-uuid-2"],  # Pre-existing source_uuids
        },
        {
            "uuid": company2_uuid,
            "name": "Acme Corp",
            "description": "A company",
            "source_uuids": ["old-uuid-3", "old-uuid-4"],  # Pre-existing source_uuids
        },
    ]

    # Create the block structure
    block = {
        "block_key": "ACME",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    # Create a mock BAML client
    mock_baml_client = AsyncMock()

    # Mock the BAML response
    # According to the BAML prompt, it should accumulate:
    # - The IDs of companies being merged (1, 2)
    # - The source_ids from those companies (3, 4, 5, 6 for the historical UUIDs)
    # Since company1 has source_uuids ["old-uuid-1", "old-uuid-2"] -> IDs 3, 4
    # And company2 has source_uuids ["old-uuid-3", "old-uuid-4"] -> IDs 5, 6
    merged_company = MockCompany(
        id=100,  # New ID for merged company
        source_ids=[1, 2, 3, 4, 5, 6],  # All accumulated IDs per BAML prompt
        name="Acme Corporation",
    )

    mock_baml_client.MultiEntityResolution.return_value = MockResolvedCompanyList([merged_company])

    # Run the function
    result = await process_block_with_uuid_mapping(block, mock_baml_client)

    # Verify the result
    assert result["was_resolved"] is True
    assert len(result["resolved_companies"]) == 1

    resolved_company = result["resolved_companies"][0]

    # Check that source_uuids contains:
    # 1. The UUIDs of the merged companies (company1_uuid, company2_uuid)
    # 2. All the pre-existing source_uuids from both companies
    expected_source_uuids = {
        company1_uuid,  # Company 1's UUID
        company2_uuid,  # Company 2's UUID
        "old-uuid-1",  # Company 1's pre-existing source_uuids
        "old-uuid-2",
        "old-uuid-3",  # Company 2's pre-existing source_uuids
        "old-uuid-4",
    }

    actual_source_uuids = (
        set(resolved_company["source_uuids"]) if resolved_company["source_uuids"] else set()
    )

    logger.info(f"Expected source_uuids: {expected_source_uuids}")
    logger.info(f"Actual source_uuids: {actual_source_uuids}")

    missing_uuids = expected_source_uuids - actual_source_uuids
    assert len(missing_uuids) == 0, f"Missing UUIDs in accumulation: {missing_uuids}"

    # Verify the count
    assert len(actual_source_uuids) == 6, (
        f"Should have 6 source_uuids, got {len(actual_source_uuids)}"
    )

    logger.info("✅ UUID accumulation test passed - all source_uuids properly accumulated")


@pytest.mark.asyncio
async def test_uuid_accumulation_without_existing_source_uuids():
    """
    Test UUID accumulation when companies don't have pre-existing source_uuids.
    """
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())
    company3_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "Company A",
            "description": "First company",
            # No source_uuids
        },
        {
            "uuid": company2_uuid,
            "name": "Company A",
            "description": "Second company",
            # No source_uuids
        },
        {
            "uuid": company3_uuid,
            "name": "Company A",
            "description": "Third company",
            # No source_uuids
        },
    ]

    block = {
        "block_key": "COMPANY_A",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    # Mock BAML client
    mock_baml_client = AsyncMock()

    # BAML merges all three companies (IDs 1, 2, 3)
    merged_company = MockCompany(
        id=200,
        source_ids=[1, 2, 3],  # All three companies were merged
        name="Company A",
    )

    mock_baml_client.MultiEntityResolution.return_value = MockResolvedCompanyList([merged_company])

    # Run the function
    result = await process_block_with_uuid_mapping(block, mock_baml_client)

    # Verify
    assert result["was_resolved"] is True
    resolved_company = result["resolved_companies"][0]

    # Should have the three original UUIDs as source_uuids
    expected_source_uuids = {company1_uuid, company2_uuid, company3_uuid}
    actual_source_uuids = (
        set(resolved_company["source_uuids"]) if resolved_company["source_uuids"] else set()
    )

    missing_uuids = expected_source_uuids - actual_source_uuids
    assert len(missing_uuids) == 0, f"Missing UUIDs: {missing_uuids}"

    logger.info("✅ UUID accumulation without pre-existing source_uuids passed")


@pytest.mark.asyncio
async def test_uuid_accumulation_partial_merge():
    """
    Test UUID accumulation when only some companies are merged.
    """
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())
    company3_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "Company X",
            "description": "First",
            "source_uuids": ["prev-uuid-1"],
        },
        {
            "uuid": company2_uuid,
            "name": "Company Y",
            "description": "Second",
            "source_uuids": ["prev-uuid-2"],
        },
        {
            "uuid": company3_uuid,
            "name": "Company Z",
            "description": "Third",
            "source_uuids": ["prev-uuid-3"],
        },
    ]

    block = {
        "block_key": "XYZ",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    mock_baml_client = AsyncMock()

    # BAML merges companies 1 and 2, but keeps 3 separate
    # Company 1 has source_uuids ["prev-uuid-1"] -> ID 4
    # Company 2 has source_uuids ["prev-uuid-2"] -> ID 5
    # Company 3 has source_uuids ["prev-uuid-3"] -> ID 6
    merged_company_1_2 = MockCompany(
        id=300,
        source_ids=[1, 2, 4, 5],  # Companies 1, 2 and their source_ids
        name="Company XY",
    )

    separate_company_3 = MockCompany(
        id=3,  # When not merged, BAML keeps the same ID
        source_ids=[3, 6],  # Company 3 and its source_ids
        name="Company Z",
    )

    mock_baml_client.MultiEntityResolution.return_value = MockResolvedCompanyList(
        [merged_company_1_2, separate_company_3]
    )

    # Run the function
    result = await process_block_with_uuid_mapping(block, mock_baml_client)

    # Verify
    assert result["was_resolved"] is True
    assert len(result["resolved_companies"]) == 2

    # Check the merged company (1 and 2)
    merged = result["resolved_companies"][0]
    merged_source_uuids = set(merged["source_uuids"]) if merged["source_uuids"] else set()

    expected_merged = {
        company1_uuid,
        company2_uuid,
        "prev-uuid-1",
        "prev-uuid-2",
    }

    missing_merged = expected_merged - merged_source_uuids
    assert len(missing_merged) == 0, f"Missing UUIDs in merged company: {missing_merged}"

    # Check the separate company (3)
    separate = result["resolved_companies"][1]
    separate_source_uuids = set(separate["source_uuids"]) if separate["source_uuids"] else set()

    expected_separate = {
        company3_uuid,
        "prev-uuid-3",
    }

    missing_separate = expected_separate - separate_source_uuids
    assert len(missing_separate) == 0, f"Missing UUIDs in separate company: {missing_separate}"

    logger.info("✅ Partial merge UUID accumulation test passed")


@pytest.mark.asyncio
async def test_single_company_block():
    """
    Test that single company blocks are handled correctly.
    """
    company_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company_uuid,
            "name": "Solo Company",
            "description": "Single company",
            "source_uuids": ["old-1", "old-2"],
        }
    ]

    block = {
        "block_key": "SOLO",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    mock_baml_client = AsyncMock()

    # The function should handle single companies without calling BAML
    result = await process_block_with_uuid_mapping(block, mock_baml_client)

    # Verify BAML was not called for single company
    mock_baml_client.MultiEntityResolution.assert_not_called()

    # Verify the result
    assert result["was_resolved"] is False  # Single companies aren't "resolved"
    assert len(result["resolved_companies"]) == 1

    company = result["resolved_companies"][0]
    source_uuids = set(company["source_uuids"]) if company["source_uuids"] else set()

    # Should have the company's UUID plus existing source_uuids
    expected = {company_uuid, "old-1", "old-2"}

    missing = expected - source_uuids
    assert len(missing) == 0, f"Missing UUIDs: {missing}"

    logger.info("✅ Single company block test passed")


if __name__ == "__main__":
    # Run tests directly
    import sys

    logging.basicConfig(level=logging.INFO)

    async def run_all_tests():
        """Run all tests."""
        try:
            await test_uuid_accumulation_with_existing_source_uuids()
            await test_uuid_accumulation_without_existing_source_uuids()
            await test_uuid_accumulation_partial_merge()
            await test_single_company_block()
            print("\n" + "=" * 60)
            print("ALL UUID ACCUMULATION TESTS PASSED ✅")
            print("=" * 60)
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            sys.exit(1)

    asyncio.run(run_all_tests())

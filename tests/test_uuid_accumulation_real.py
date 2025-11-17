#!/usr/bin/env python3
"""Test UUID accumulation with real BAML client."""

import asyncio
import logging
import uuid as uuid_mod

import pytest

from abzu.baml_client import b as baml_client
from abzu.er.uuid import process_block_with_uuid_mapping
from abzu.logs import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
async def test_uuid_accumulation_with_real_baml():
    """
    Test UUID accumulation using the real BAML client.
    This tests that the mapping from UUIDs to IDs and back works correctly
    when companies with existing source_uuids are merged.
    """
    # Create test companies with pre-existing source_uuids
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "Tesla, Inc.",
            "ticker": {
                "symbol": "TSLA",
                "exchange": "NASDAQ",
            },
            "description": "Tesla is a leader in electric transportation and energy storage",
            "founded_year": 2003,
            "ceo": "Elon Musk",
            "source_uuids": ["old-uuid-1", "old-uuid-2"],  # Pre-existing source_uuids
        },
        {
            "uuid": company2_uuid,
            "name": "Tesla",
            "ticker": {
                "symbol": "TSLA",
            },
            "description": "Tesla is known for its electric car innovations",
            "headquarters_location": "Austin, United States",
            "source_uuids": ["old-uuid-3", "old-uuid-4"],  # Pre-existing source_uuids
        },
    ]

    # Create the block structure
    block = {
        "block_key": "TESLA",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    # Run the function with real BAML client
    result = await process_block_with_uuid_mapping(block, baml_client)

    # Verify the result
    assert result["was_resolved"] is True
    assert len(result["resolved_companies"]) == 1, "Should merge into one company"

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
    assert (
        len(actual_source_uuids) == 6
    ), f"Should have 6 source_uuids, got {len(actual_source_uuids)}"

    logger.info(
        "✅ Real BAML UUID accumulation test passed - all source_uuids properly accumulated"
    )


@pytest.mark.asyncio
async def test_partial_merge_with_real_baml():
    """
    Test UUID accumulation when only some companies are merged using real BAML.
    """
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())
    company3_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "NVIDIA Corporation",
            "ticker": {"symbol": "NVDA", "exchange": "NASDAQ"},
            "description": "Leading AI and GPU technology company",
            "headquarters_location": "Santa Clara, CA",
            "founded_year": 1993,
            "ceo": "Jensen Huang",
            "source_uuids": ["prev-uuid-1", "prev-uuid-2"],
        },
        {
            "uuid": company2_uuid,
            "name": "NVIDIA",
            "ticker": {"symbol": "NVDA"},
            "description": "Graphics processing unit manufacturer",
            "website_url": "https://nvidia.com",
            "revenue_usd": 26974000000,
            "employees": 22473,
            "source_uuids": ["prev-uuid-3", "prev-uuid-4"],
        },
        {
            "uuid": company3_uuid,
            "name": "Intel Corporation",  # Different company
            "ticker": {"symbol": "INTC"},
            "description": "Semiconductor chip manufacturer",
            "headquarters_location": "Santa Clara, CA",
            "source_uuids": ["prev-uuid-5"],
        },
    ]

    block = {
        "block_key": "TECH_COMPANIES",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    # Run with real BAML client
    result = await process_block_with_uuid_mapping(block, baml_client)

    # Verify
    assert result["was_resolved"] is True

    # BAML should merge the two NVIDIA entries but keep Intel separate
    assert len(result["resolved_companies"]) == 2, "Should have 2 companies after merge"

    # Find which is NVIDIA and which is Intel
    nvidia_company = None
    intel_company = None

    for company in result["resolved_companies"]:
        if "NVIDIA" in company["name"] or "Nvidia" in company["name"]:
            nvidia_company = company
        elif "Intel" in company["name"]:
            intel_company = company

    assert nvidia_company is not None, "Should have NVIDIA in results"
    assert intel_company is not None, "Should have Intel in results"

    # Check NVIDIA merged company
    nvidia_source_uuids = (
        set(nvidia_company["source_uuids"]) if nvidia_company["source_uuids"] else set()
    )
    expected_nvidia = {
        company1_uuid,
        company2_uuid,
        "prev-uuid-1",
        "prev-uuid-2",
        "prev-uuid-3",
        "prev-uuid-4",
    }

    missing_nvidia = expected_nvidia - nvidia_source_uuids
    assert len(missing_nvidia) == 0, f"Missing UUIDs in NVIDIA company: {missing_nvidia}"

    # Check Intel separate company
    intel_source_uuids = (
        set(intel_company["source_uuids"]) if intel_company["source_uuids"] else set()
    )
    expected_intel = {
        company3_uuid,
        "prev-uuid-5",
    }

    missing_intel = expected_intel - intel_source_uuids
    assert len(missing_intel) == 0, f"Missing UUIDs in Intel company: {missing_intel}"

    logger.info("✅ Partial merge with real BAML test passed")


@pytest.mark.asyncio
async def test_no_existing_source_uuids_with_real_baml():
    """
    Test UUID accumulation when companies don't have pre-existing source_uuids.
    """
    company1_uuid = str(uuid_mod.uuid4())
    company2_uuid = str(uuid_mod.uuid4())

    companies_data = [
        {
            "uuid": company1_uuid,
            "name": "Apple Inc.",
            "ticker": {"symbol": "AAPL"},
            "description": "Technology company that designs consumer electronics",
            "headquarters_location": "Cupertino, CA",
            # No source_uuids
        },
        {
            "uuid": company2_uuid,
            "name": "Apple",
            "ticker": {"symbol": "AAPL"},
            "description": "iPhone and Mac manufacturer",
            "ceo": "Tim Cook",
            # No source_uuids
        },
    ]

    block = {
        "block_key": "APPLE",
        "block_key_type": "combined",
        "companies": companies_data,
    }

    # Run with real BAML client
    result = await process_block_with_uuid_mapping(block, baml_client)

    # Verify
    assert result["was_resolved"] is True
    assert len(result["resolved_companies"]) == 1, "Should merge into one company"

    resolved_company = result["resolved_companies"][0]

    # Should have the two original UUIDs as source_uuids
    expected_source_uuids = {company1_uuid, company2_uuid}
    actual_source_uuids = (
        set(resolved_company["source_uuids"]) if resolved_company["source_uuids"] else set()
    )

    missing_uuids = expected_source_uuids - actual_source_uuids
    assert len(missing_uuids) == 0, f"Missing UUIDs: {missing_uuids}"

    logger.info("✅ No pre-existing source_uuids with real BAML test passed")


if __name__ == "__main__":
    # Run tests directly
    import sys

    logging.basicConfig(level=logging.INFO)

    async def run_all_tests():
        """Run all tests."""
        try:
            await test_uuid_accumulation_with_real_baml()
            await test_partial_merge_with_real_baml()
            await test_no_existing_source_uuids_with_real_baml()
            print("\n" + "=" * 60)
            print("ALL REAL BAML UUID ACCUMULATION TESTS PASSED ✅")
            print("=" * 60)
        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            sys.exit(1)

    asyncio.run(run_all_tests())

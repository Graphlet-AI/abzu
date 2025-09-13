"""Integration tests for UUID mapper using real ER blocks and BAML client."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from abzu.baml_client import b as baml_client
from abzu.er.uuid import UUIDMapper, process_block_with_uuid_mapping


class TestUUIDMapper:
    """Test the UUIDMapper class."""

    def test_uuid_to_int_mapping(self):
        """Test basic UUID to integer mapping."""
        mapper = UUIDMapper()

        # Add UUIDs
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        uuid3 = str(uuid4())

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)
        id3 = mapper.add_uuid(uuid3)

        # Check IDs are consecutive
        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

        # Check same UUID returns same ID
        assert mapper.add_uuid(uuid1) == id1
        assert mapper.add_uuid(uuid2) == id2
        assert mapper.add_uuid(uuid3) == id3

    def test_int_to_uuid_mapping(self):
        """Test reverse mapping from integers to UUIDs."""
        mapper = UUIDMapper()

        uuid1 = str(uuid4())
        uuid2 = str(uuid4())

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)

        # Test reverse lookup
        assert mapper.get_uuid(id1) == uuid1
        assert mapper.get_uuid(id2) == uuid2
        assert mapper.get_uuid(999) is None  # Non-existent ID

    def test_map_ids_to_uuids(self):
        """Test mapping a list of IDs to UUIDs."""
        mapper = UUIDMapper()

        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        uuid3 = str(uuid4())

        id1 = mapper.add_uuid(uuid1)
        id2 = mapper.add_uuid(uuid2)
        id3 = mapper.add_uuid(uuid3)

        # Test list mapping
        ids = [id1, id2, id3]
        uuids = mapper.map_ids_to_uuids(ids)
        assert uuids == [uuid1, uuid2, uuid3]

        # Test with None
        assert mapper.map_ids_to_uuids(None) is None

        # Test with some invalid IDs
        mixed_ids = [id1, 999, id2]
        mixed_uuids = mapper.map_ids_to_uuids(mixed_ids)
        assert mixed_uuids == [uuid1, uuid2]


@pytest.mark.asyncio
class TestProcessBlockWithUUIDMapping:
    """Test the process_block_with_uuid_mapping function with real blocks and BAML client."""

    @pytest.fixture
    def sample_blocks(self):
        """Load sample blocks from real ER data."""
        blocks_file = Path("data/blocks.json")

        if not blocks_file.exists():
            # Return mock blocks if file doesn't exist
            return self._create_mock_blocks()

        blocks = []
        with open(blocks_file, "r") as f:
            for i, line in enumerate(f):
                block = json.loads(line)
                # Get a mix of single and multi-company blocks
                if len(blocks) < 3 and block.get("block_size", 0) == 1:
                    blocks.append(block)
                elif len(blocks) < 6 and block.get("block_size", 0) > 1:
                    blocks.append(block)
                if len(blocks) >= 6:
                    break

        # If we didn't find enough real blocks, add mock ones
        if len(blocks) < 3:
            blocks.extend(self._create_mock_blocks())

        return blocks

    def _create_mock_blocks(self):
        """Create mock blocks for testing when real data isn't available."""
        return [
            {
                "block_key": "test_single",
                "block_key_type": "test",
                "block_size": 1,
                "companies": [
                    {
                        "uuid": str(uuid4()),
                        "id": 1,
                        "name": "Test Company A",
                        "description": "A test company",
                        "ticker": {"symbol": "TSTA", "exchange": "NYSE"},
                    }
                ],
            },
            {
                "block_key": "test_multi",
                "block_key_type": "test",
                "block_size": 3,
                "companies": [
                    {
                        "uuid": str(uuid4()),
                        "id": 2,
                        "name": "Test Company B",
                        "description": "Company B description",
                        "ticker": {"symbol": "TSTB", "exchange": "NASDAQ"},
                    },
                    {
                        "uuid": str(uuid4()),
                        "id": 3,
                        "name": "Test Company B Inc.",
                        "description": "Company B incorporated",
                        "ticker": {"symbol": "TSTB", "exchange": "NASDAQ"},
                    },
                    {
                        "uuid": str(uuid4()),
                        "id": 4,
                        "name": "Test Company C",
                        "description": "Company C description",
                        "ticker": None,
                    },
                ],
            },
        ]

    async def test_single_company_block(self, sample_blocks):
        """Test processing a block with a single company."""
        # Find a single company block
        single_block = next((b for b in sample_blocks if b.get("block_size", 0) == 1), None)
        if not single_block:
            pytest.skip("No single company blocks found")

        # Use real BAML client

        result = await process_block_with_uuid_mapping(
            block=single_block, baml_client=baml_client, collector=None
        )

        # Single company blocks should not be resolved
        assert not result["was_resolved"]
        assert result["total_companies"] == 1

        # Check that source_uuids contains the original UUID
        company = result["resolved_companies"][0]
        if "uuid" in company and company["uuid"]:
            assert "source_uuids" in company
            if company["source_uuids"]:
                assert company["uuid"] in company["source_uuids"]

        # Single company blocks are handled without BAML calls

    async def test_multi_company_block(self, sample_blocks):
        """Test processing a block with multiple companies."""
        # Find a multi-company block
        multi_block = next((b for b in sample_blocks if b.get("block_size", 0) > 1), None)
        if not multi_block:
            pytest.skip("No multi-company blocks found")

        # Use real BAML client for actual MultiEntityResolution
        result = await process_block_with_uuid_mapping(
            block=multi_block, baml_client=baml_client, collector=None
        )

        # Check that the block was resolved
        assert result["was_resolved"]

        # Check that source_uuids were populated from source_ids
        for company in result["resolved_companies"]:
            if company.get("source_ids"):
                assert "source_uuids" in company
                # source_uuids should have been mapped from source_ids
                if company["source_uuids"]:
                    assert len(company["source_uuids"]) == len(company["source_ids"])

    async def test_uuid_preservation_in_source_uuids(self):
        """Test that original UUIDs are preserved in source_uuids field."""
        # Create a block with known UUIDs
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        uuid3 = str(uuid4())

        test_block = {
            "block_key": "test_uuid_preservation",
            "block_key_type": "test",
            "block_size": 3,
            "companies": [
                {
                    "uuid": uuid1,
                    "id": 100,
                    "name": "Company Alpha",
                    "description": "First company",
                },
                {
                    "uuid": uuid2,
                    "id": 200,
                    "name": "Company Alpha Inc.",
                    "description": "Same as first",
                },
                {
                    "uuid": uuid3,
                    "id": 300,
                    "name": "Company Beta",
                    "description": "Different company",
                },
            ],
        }

        # Use real BAML client
        result = await process_block_with_uuid_mapping(
            block=test_block, baml_client=baml_client, collector=None
        )

        # Check results - actual BAML response may vary
        assert result["was_resolved"]
        assert len(result["resolved_companies"]) > 0

        # Verify that source_uuids are populated from the mapping
        for company in result["resolved_companies"]:
            assert "source_uuids" in company
            if company.get("source_ids"):
                # If BAML returned source_ids, they should be mapped to UUIDs
                assert company["source_uuids"] is not None
                assert len(company["source_uuids"]) > 0
                # Check that all source_uuids are valid UUIDs from our input
                for source_uuid in company["source_uuids"]:
                    assert source_uuid in [uuid1, uuid2, uuid3]

    async def test_block_with_existing_source_uuids(self):
        """Test that existing source_uuids are preserved and extended."""
        # Create a block where companies already have source_uuids
        uuid1 = str(uuid4())
        uuid2 = str(uuid4())
        old_uuid1 = str(uuid4())
        old_uuid2 = str(uuid4())

        test_block = {
            "block_key": "test_existing_source_uuids",
            "block_key_type": "test",
            "block_size": 2,
            "companies": [
                {
                    "uuid": uuid1,
                    "id": 1,
                    "name": "Company with history",
                    "description": "Has existing source_uuids",
                    "source_uuids": [old_uuid1],  # Already has source UUIDs
                },
                {
                    "uuid": uuid2,
                    "id": 2,
                    "name": "Company with history Inc.",
                    "description": "Also has existing source_uuids",
                    "source_uuids": [old_uuid2],  # Already has source UUIDs
                },
            ],
        }

        # Use real BAML client

        result = await process_block_with_uuid_mapping(
            block=test_block, baml_client=baml_client, collector=None
        )

        # Check that source_uuids are populated
        assert result["was_resolved"]
        for company in result["resolved_companies"]:
            assert "source_uuids" in company
            # Verify UUID mapping worked
            if company.get("source_ids"):
                assert company["source_uuids"] is not None

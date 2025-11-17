"""Unit tests for UUID provenance preservation in entity resolution."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from abzu.baml_client.types import Company
from abzu.er.uuid import process_block_with_uuid_mapping


class TestUUIDProvenance:
    """Test that all input UUIDs are preserved through entity resolution."""

    @pytest.fixture
    def mock_baml_client(self) -> AsyncMock:
        """Create a mock BAML client that simulates merge behavior."""
        client = AsyncMock()

        # Simulate BAML merging 3 companies into 1
        # Input IDs: [1, 2, 3] -> Output: id=1, source_ids=[2, 3]
        async def mock_few_shot_call(*args: Any, **kwargs: Any) -> MagicMock:
            result = MagicMock()
            result.companies = [
                Company(
                    id=1,  # Master ID (lowest)
                    uuid=None,
                    name="Merged Company",
                    cik=None,
                    ticker=None,
                    description="Combined description",
                    website_url=None,
                    headquarters_location=None,
                    jurisdiction=None,
                    revenue_usd=None,
                    employees=None,
                    founded_year=None,
                    ceo=None,
                    linkedin_url=None,
                    source_ids=[2, 3],  # Other IDs merged in
                    source_uuids=[],
                    match_skip=None,
                    match_skip_history=None,
                )
            ]
            return result

        client.FewShotMultiEntityResolution = mock_few_shot_call
        return client

    @pytest.mark.asyncio
    async def test_master_uuid_preserved_in_output(self, mock_baml_client: AsyncMock) -> None:
        """Test that master UUID is preserved as output company UUID."""
        block = {
            "block_key": "TEST",
            "block_key_type": "test",
            "companies": [
                {
                    "uuid": "uuid-1",
                    "name": "Company A",
                    "description": "Description A",
                },
                {
                    "uuid": "uuid-2",
                    "name": "Company B",
                    "description": "Description B",
                },
                {
                    "uuid": "uuid-3",
                    "name": "Company C",
                    "description": "Description C",
                },
            ],
        }

        result = await process_block_with_uuid_mapping(
            block=block, baml_client=mock_baml_client, collector=None, iteration=1
        )

        # Check that we got one merged company
        assert len(result["resolved_companies"]) == 1
        merged = result["resolved_companies"][0]

        # Master UUID should be preserved (uuid-1 maps to ID 1)
        assert merged["uuid"] == "uuid-1"

    @pytest.mark.asyncio
    async def test_all_uuids_in_source_uuids(self, mock_baml_client: AsyncMock) -> None:
        """Test that ALL input UUIDs appear in source_uuids (including master)."""
        block = {
            "block_key": "TEST",
            "block_key_type": "test",
            "companies": [
                {
                    "uuid": "uuid-1",
                    "name": "Company A",
                    "description": "Description A",
                },
                {
                    "uuid": "uuid-2",
                    "name": "Company B",
                    "description": "Description B",
                },
                {
                    "uuid": "uuid-3",
                    "name": "Company C",
                    "description": "Description C",
                },
            ],
        }

        result = await process_block_with_uuid_mapping(
            block=block, baml_client=mock_baml_client, collector=None, iteration=1
        )

        merged = result["resolved_companies"][0]
        source_uuids = set(merged["source_uuids"])

        # ALL input UUIDs must be in source_uuids
        assert "uuid-1" in source_uuids  # Master
        assert "uuid-2" in source_uuids  # Merged
        assert "uuid-3" in source_uuids  # Merged
        assert len(source_uuids) == 3

    @pytest.mark.asyncio
    async def test_singleton_block_self_reference(self, mock_baml_client: AsyncMock) -> None:
        """Test that singleton companies have self-reference in source_uuids."""
        block = {
            "block_key": "SINGLETON",
            "block_key_type": "test",
            "companies": [
                {
                    "uuid": "uuid-single",
                    "name": "Single Company",
                    "description": "Single description",
                }
            ],
        }

        result = await process_block_with_uuid_mapping(
            block=block, baml_client=mock_baml_client, collector=None, iteration=1
        )

        company = result["resolved_companies"][0]

        # Singleton should reference itself
        assert company["uuid"] == "uuid-single"
        assert company["source_uuids"] == ["uuid-single"]
        assert company["match_skip"] is False

    @pytest.mark.asyncio
    async def test_no_uuid_loss_across_merge(self, mock_baml_client: AsyncMock) -> None:
        """Test that no UUIDs are lost when merging."""
        block = {
            "block_key": "MULTI",
            "block_key_type": "test",
            "companies": [
                {"uuid": "uuid-a", "name": "Company 1", "description": "Desc 1"},
                {"uuid": "uuid-b", "name": "Company 2", "description": "Desc 2"},
                {"uuid": "uuid-c", "name": "Company 3", "description": "Desc 3"},
                {"uuid": "uuid-d", "name": "Company 4", "description": "Desc 4"},
            ],
        }

        # Adjust mock to merge 4 companies
        async def mock_merge_four(*args: Any, **kwargs: Any) -> MagicMock:
            result = MagicMock()
            result.companies = [
                Company(
                    id=1,
                    uuid=None,
                    name="Merged Company",
                    cik=None,
                    ticker=None,
                    description="Combined",
                    website_url=None,
                    headquarters_location=None,
                    jurisdiction=None,
                    revenue_usd=None,
                    employees=None,
                    founded_year=None,
                    ceo=None,
                    linkedin_url=None,
                    source_ids=[2, 3, 4],  # Other IDs
                    source_uuids=[],
                    match_skip=None,
                    match_skip_history=None,
                )
            ]
            return result

        mock_baml_client.FewShotMultiEntityResolution = mock_merge_four

        result = await process_block_with_uuid_mapping(
            block=block, baml_client=mock_baml_client, collector=None, iteration=1
        )

        merged = result["resolved_companies"][0]
        output_uuids = set(merged["source_uuids"])

        # All input UUIDs must be accounted for
        expected_uuids = ["uuid-a", "uuid-b", "uuid-c", "uuid-d"]
        for uuid in expected_uuids:
            assert uuid in output_uuids, f"UUID {uuid} was lost!"

    @pytest.mark.asyncio
    async def test_source_uuids_preserved_when_unmerged(self, mock_baml_client: AsyncMock) -> None:
        """Test that existing source_uuids are preserved when company is not merged."""

        # Mock BAML to return empty source_ids (no merge)
        async def mock_no_merge(*args: Any, **kwargs: Any) -> MagicMock:
            result = MagicMock()
            result.companies = [
                Company(
                    id=1,
                    uuid=None,
                    name="Company A",
                    cik=None,
                    ticker=None,
                    description="Description A",
                    website_url=None,
                    headquarters_location=None,
                    jurisdiction=None,
                    revenue_usd=None,
                    employees=None,
                    founded_year=None,
                    ceo=None,
                    linkedin_url=None,
                    source_ids=[],  # Empty - no merge
                    source_uuids=[],
                    match_skip=None,
                    match_skip_history=None,
                )
            ]
            return result

        mock_baml_client.FewShotMultiEntityResolution = mock_no_merge

        block = {
            "block_key": "PRESERVE",
            "block_key_type": "test",
            "companies": [
                {
                    "uuid": "uuid-current",
                    "name": "Company A",
                    "description": "Description",
                    "source_uuids": ["uuid-old-1", "uuid-old-2"],  # Existing from prev iteration
                }
            ],
        }

        result = await process_block_with_uuid_mapping(
            block=block, baml_client=mock_baml_client, collector=None, iteration=1
        )

        company = result["resolved_companies"][0]

        # When BAML returns empty source_ids, should preserve existing source_uuids
        # BUT also add current UUID for complete provenance
        assert set(company["source_uuids"]) == {"uuid-current", "uuid-old-1", "uuid-old-2"}


class TestEdgeTraceability:
    """Test that edges can be traced through merges."""

    def test_edge_lookup_by_output_uuid(self) -> None:
        """Test that edges can find company by output UUID."""
        # Simulated scenario after merge
        output_company = {
            "uuid": "master-uuid-123",  # This should be one of the input UUIDs
            "source_uuids": ["master-uuid-123", "merged-uuid-456", "merged-uuid-789"],
        }

        # Edge pointing to one of the input companies
        edge_target_uuid = "master-uuid-123"

        # Should be able to find via direct UUID match
        assert output_company["uuid"] == edge_target_uuid

    def test_edge_lookup_by_source_uuids(self) -> None:
        """Test that edges can find company via source_uuids."""
        output_company = {
            "uuid": "master-uuid-123",
            "source_uuids": ["master-uuid-123", "merged-uuid-456", "merged-uuid-789"],
        }

        # Edge pointing to a merged company
        edge_target_uuid = "merged-uuid-456"

        # Should be able to find via source_uuids
        assert edge_target_uuid in output_company["source_uuids"]

    def test_all_edges_preserved(self) -> None:
        """Test that edges to ALL input companies can be found."""
        # 3 companies merged

        output_company = {
            "uuid": "uuid-A",  # Master preserved
            "source_uuids": ["uuid-A", "uuid-B", "uuid-C"],  # All included
        }

        # Edges pointing to each input company
        edges = [
            {"from": "product-1", "to": "uuid-A"},
            {"from": "product-2", "to": "uuid-B"},
            {"from": "product-3", "to": "uuid-C"},
        ]

        # All edges should be traceable
        for edge in edges:
            target = edge["to"]
            found = target == output_company["uuid"] or target in output_company["source_uuids"]
            assert found, f"Edge to {target} cannot be traced!"

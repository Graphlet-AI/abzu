"""UUID to integer ID mapping wrapper for MultiEntityResolution API."""

import copy
from typing import Any, Optional

from abzu.baml_client.async_client import BamlAsyncClient
from abzu.baml_client.runtime import BamlCallOptions
from abzu.baml_client.types import Company, CompanyList
from abzu.logs import get_logger

logger = get_logger(__name__)


class UUIDMapper:
    """Maps UUIDs to integer IDs for BAML processing and back."""

    def __init__(self):
        """Initialize the UUID mapper."""
        self.uuid_to_int: dict[str, int] = {}
        self.int_to_uuid: dict[int, str] = {}
        self.next_id = 1

    def add_uuid(self, uuid: str) -> int:
        """
        Add a UUID to the mapping and return its integer ID.

        Args:
            uuid: The UUID string to map

        Returns:
            The integer ID for this UUID
        """
        if uuid not in self.uuid_to_int:
            self.uuid_to_int[uuid] = self.next_id
            self.int_to_uuid[self.next_id] = uuid
            self.next_id += 1
        return self.uuid_to_int[uuid]

    def get_uuid(self, int_id: int) -> Optional[str]:
        """
        Get the UUID for a given integer ID.

        Args:
            int_id: The integer ID to look up

        Returns:
            The UUID string, or None if not found
        """
        return self.int_to_uuid.get(int_id)

    def map_ids_to_uuids(self, ids: Optional[list[int]]) -> Optional[list[str]]:
        """
        Map a list of integer IDs back to UUIDs.

        Args:
            ids: List of integer IDs

        Returns:
            List of UUID strings, or None if input is None
        """
        if ids is None:
            return None
        uuids = []
        for id_val in ids:
            uuid = self.get_uuid(id_val)
            if uuid:
                uuids.append(uuid)
            else:
                logger.warning(f"No UUID found for integer ID {id_val}")
        return uuids if uuids else None


async def process_block_with_uuid_mapping(
    block: dict[str, Any],
    baml_client: BamlAsyncClient,
    collector: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Process a block using MultiEntityResolution with UUID to integer ID mapping.

    This function:
    1. Maps UUIDs to consecutive integer IDs
    2. Submits the modified data to MultiEntityResolution
    3. Maps the returned source_ids back to source_uuids

    Args:
        block: Dictionary containing block data with companies list
        baml_client: The BAML async client instance
        collector: Optional collector for BAML options

    Returns:
        Dictionary with matched/resolved companies with source_uuids restored
    """
    block_key = block["block_key"]
    block_key_type = block["block_key_type"]
    companies_data = block["companies"]

    # Skip blocks with only one company
    if len(companies_data) <= 1:
        # For single companies, ensure source_uuids contains the UUID
        if len(companies_data) == 1:
            company = companies_data[0]
            if "uuid" in company and company["uuid"]:
                if "source_uuids" not in company or not company["source_uuids"]:
                    company["source_uuids"] = [company["uuid"]]
                elif (
                    isinstance(company["source_uuids"], list)
                    and company["uuid"] not in company["source_uuids"]
                ):
                    company["source_uuids"].append(company["uuid"])

        return {
            "block_key": block_key,
            "block_key_type": block_key_type,
            "resolved_companies": companies_data,
            "total_companies": len(companies_data),
            "was_resolved": False,
        }

    try:
        logger.info(f"Processing block '{block_key}' with {len(companies_data)} companies")

        # Create UUID mapper for this block
        mapper = UUIDMapper()

        # Convert companies to Company objects with integer IDs
        companies = []
        original_uuid_mapping = {}  # Track original UUID for each company

        for comp_data in companies_data:
            # Deep copy to avoid modifying original data
            comp_copy = copy.deepcopy(comp_data)

            # Map UUID to integer ID if present
            original_uuid = comp_copy.get("uuid")
            if original_uuid:
                int_id = mapper.add_uuid(original_uuid)
                original_uuid_mapping[int_id] = original_uuid
                # Replace UUID with integer ID for BAML processing
                comp_copy["id"] = int_id
                # Clear UUID and source_uuids for BAML - it works better with integers
                comp_copy["uuid"] = None
                comp_copy["source_uuids"] = None
            else:
                # If no UUID, ensure we have an integer ID
                if "id" not in comp_copy or comp_copy["id"] is None:
                    comp_copy["id"] = mapper.next_id
                    mapper.next_id += 1

            # Create Company object
            company = Company(
                id=comp_copy["id"],  # Use the integer ID
                uuid=None,  # Clear UUID for BAML
                name=comp_copy["name"],
                description=comp_copy.get("description", ""),
                ceo=comp_copy.get("ceo"),
                cik=comp_copy.get("cik"),
                employees=comp_copy.get("employees"),
                founded_year=comp_copy.get("founded_year"),
                headquarters_location=comp_copy.get("headquarters_location"),
                jurisdiction=comp_copy.get("jurisdiction"),
                linkedin_url=comp_copy.get("linkedin_url"),
                revenue_usd=comp_copy.get("revenue_usd"),
                source_ids=comp_copy.get("source_ids"),
                source_uuids=None,  # Clear for BAML
                ticker=comp_copy.get("ticker"),
                website_url=comp_copy.get("website_url"),
            )
            companies.append(company)

        # Create CompanyList and call BAML function
        company_list = CompanyList(
            block_key=block_key,
            block_key_type=block_key_type,
            block_size=len(companies),
            companies=companies,
        )

        logger.debug(
            f"Submitting block '{block_key}' to MultiEntityResolution API with integer IDs"
        )

        # Call BAML with integer IDs
        if collector:
            baml_options = BamlCallOptions(collector=collector)
            result = await baml_client.MultiEntityResolution(
                company_list=company_list, baml_options=baml_options
            )
        else:
            result = await baml_client.MultiEntityResolution(company_list=company_list)

        # Convert resolved companies back to dictionaries with UUID mapping restored
        resolved_companies = []
        for company in result.companies:
            resolved_dict = {
                "uuid": company.uuid,  # Will be assigned a new UUID later
                "block_key": block_key,
                "block_key_type": block_key_type,
                "url": None,
                "name": company.name,
                "description": company.description,
                "ceo": company.ceo,
                "cik": company.cik,
                "employees": company.employees,
                "founded_year": company.founded_year,
                "headquarters_location": company.headquarters_location,
                "id": company.id,
                "jurisdiction": company.jurisdiction,
                "linkedin_url": company.linkedin_url,
                "posted_at": None,
                "revenue_usd": company.revenue_usd,
                "source_ids": company.source_ids,
                # Map source_ids back to source_uuids
                "source_uuids": mapper.map_ids_to_uuids(company.source_ids),
                "ticker": company.ticker.__dict__ if company.ticker else None,
                "website_url": company.website_url,
            }

            # Log the mapping for debugging
            if company.source_ids:
                logger.debug(
                    f"Mapped source_ids {company.source_ids} to source_uuids {resolved_dict['source_uuids']}"
                )

            resolved_companies.append(resolved_dict)

        logger.info(
            f"Resolved block {block_key}: {len(companies_data)} -> {len(resolved_companies)} companies "
            f"(UUID mapping restored)"
        )

        return {
            "block_key": block_key,
            "block_key_type": block_key_type,
            "original_companies": companies_data,
            "resolved_companies": resolved_companies,
            "original_count": len(companies_data),
            "resolved_count": len(resolved_companies),
            "was_resolved": True,
        }

    except Exception as e:
        logger.error(f"Error processing block {block_key}: {e}")
        # Return original companies unchanged on error
        return {
            "block_key": block_key,
            "block_key_type": block_key_type,
            "resolved_companies": companies_data,
            "total_companies": len(companies_data),
            "was_resolved": False,
            "error": str(e),
        }

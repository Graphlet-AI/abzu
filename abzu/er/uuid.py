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

    def __init__(self) -> None:
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

    def map_uuids_to_ids(self, uuids: Optional[list[str]]) -> Optional[list[int]]:
        """
        Map a list of UUIDs to their integer IDs.

        Args:
            uuids: List of UUID strings

        Returns:
            List of integer IDs, or None if input is None
        """
        if uuids is None:
            return None
        ids = [self.add_uuid(uuid) for uuid in uuids if uuid]
        return ids if ids else None


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

    # Log the input companies and their source_uuids
    logger.debug(f"Processing block {block_key} with {len(companies_data)} companies")
    for i, comp in enumerate(companies_data):
        logger.debug(
            f"  Company {i}: uuid={comp.get('uuid')}, source_uuids={comp.get('source_uuids')}"
        )

    # Skip blocks with only one company
    if len(companies_data) <= 1:
        # For single companies, ensure source_uuids contains the UUID
        if len(companies_data) == 1:
            company = companies_data[0]
            company["all_ids"] = []
            if "uuid" in company and company["uuid"]:
                company["all_ids"].append(company["uuid"])
                # Map the record's uuid into the source_uuids field so we can do a simple join on the edges
                if "source_uuids" not in company or not company["source_uuids"]:
                    company["source_uuids"] = [company["uuid"]]
                    company["all_ids"] += company["source_uuids"]
                elif (
                    isinstance(company["source_uuids"], list)
                    and company["uuid"] not in company["source_uuids"]
                ):
                    company["source_uuids"].append(company["uuid"])
                    company["all_ids"] += company["source_uuids"]

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

        for comp_data in companies_data:
            # Deep copy to avoid modifying original data
            comp_copy = copy.deepcopy(comp_data)

            # Replace UUIDs with integer IDs for BAML processing
            comp_copy["id"] = mapper.add_uuid(comp_copy.get("uuid"))
            comp_copy["uuid"] = None
            comp_copy["source_ids"] = None

            # Map old source_uuids to source_ids
            source_ids: list[int] = []
            if (
                "source_uuids" in comp_copy
                and isinstance(comp_copy["source_uuids"], list)
                and len(comp_copy["source_uuids"]) > 0
            ):
                # Map each source_uuid to an integer ID
                source_ids = [mapper.add_uuid(uuid) for uuid in comp_copy["source_uuids"] if uuid]

            # Create Company object
            company = Company(
                id=comp_copy["id"],  # Use the integer ID
                uuid=None,  # Clear UUID for BAML
                name=comp_copy["name"],
                cik=comp_copy.get("cik"),
                ticker=comp_copy.get("ticker"),
                description=comp_copy.get("description", ""),
                website_url=comp_copy.get("website_url"),
                headquarters_location=comp_copy.get("headquarters_location"),
                jurisdiction=comp_copy.get("jurisdiction"),
                revenue_usd=comp_copy.get("revenue_usd"),
                employees=comp_copy.get("employees"),
                founded_year=comp_copy.get("founded_year"),
                ceo=comp_copy.get("ceo"),
                linkedin_url=comp_copy.get("linkedin_url"),
                source_ids=source_ids,  # Send the mapped source_ids to BAML
                source_uuids=[],
                all_ids=company.get("all_ids", []),
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

            # Map the source_ids from BAML back to UUIDs
            # BAML should have accumulated all source_ids as per its prompt
            source_uuids_list = mapper.map_ids_to_uuids(company.source_ids) or []

            # BAML sometimes doesn't include the company IDs themselves in source_ids,
            # only the historical source_ids. We need to add the company UUIDs.
            # Check which companies were merged by looking at the source_ids
            source_uuids_set = set(source_uuids_list) if source_uuids_list else set()

            # Build a set of all IDs in the result for quick lookup
            result_ids = set(company.source_ids) if company.source_ids else set()

            # Add company UUIDs for companies that were merged
            for comp_data in companies_data:
                comp_uuid = comp_data.get("uuid")
                comp_id = mapper.uuid_to_int.get(comp_uuid)

                if comp_id:
                    # Check if this company's ID is in the result
                    if comp_id in result_ids:
                        source_uuids_set.add(comp_uuid)
                    # Also check if any of its historical source_ids are in the result
                    elif (
                        "source_uuids" in comp_data
                        and isinstance(comp_data["source_uuids"], list)
                        and len(comp_data["source_uuids"]) > 0
                    ):
                        for hist_uuid in comp_data["source_uuids"]:
                            hist_id = mapper.uuid_to_int.get(hist_uuid)
                            if hist_id and hist_id in result_ids:
                                # This company was merged, add its UUID
                                source_uuids_set.add(comp_uuid)
                                break

            source_uuids_final = sorted(list(source_uuids_set)) if source_uuids_set else None

            resolved_dict = {
                "id": company.id,
                "uuid": company.uuid,
                "name": company.name,
                "cik": company.cik,
                "ticker": company.ticker.__dict__ if company.ticker else None,
                "description": company.description,
                "website_url": company.website_url,
                "headquarters_location": company.headquarters_location,
                "jurisdiction": company.jurisdiction,
                "revenue_usd": company.revenue_usd,
                "employees": company.employees,
                "founded_year": company.founded_year,
                "ceo": company.ceo,
                "linkedin_url": company.linkedin_url,
                "source_ids": company.source_ids,
                "source_uuids": source_uuids_final,
                # Build all_ids from the id and source_ids - don't rely on the LLM
                "all_ids": [company.id] + (company.source_ids or []),
            }

            resolved_companies.append(resolved_dict)

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
        logger.error(f"Error processing block {block_key}: {e}", exc_info=True)
        # Return original companies unchanged on error
        return {
            "block_key": block_key,
            "block_key_type": block_key_type,
            "resolved_companies": companies_data,
            "total_companies": len(companies_data),
            "was_resolved": False,
            "error": str(e),
        }

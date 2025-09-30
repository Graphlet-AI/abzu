"""UUID to integer ID mapping wrapper for MultiEntityResolution API."""

import copy
from typing import Any, Optional

from pyspark.sql.types import Row

from abzu.baml_client.async_client import BamlAsyncClient
from abzu.baml_client.runtime import BamlCallOptions
from abzu.baml_client.types import (
    Company,
    CompanyList,
    Exchange,
    MergeCompanyExampleSet,
    Ticker,
)
from abzu.er.few_shot import company_dicts_to_baml, company_id_tracking_dicts
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
    iteration: int = 1,
) -> dict[str, Any]:
    """
    Process a block using MultiEntityResolution with UUID to integer ID mapping.

    This function:
    1. Maps UUIDs to consecutive integer IDs
    2. Submits the modified data to MultiEntityResolution
    3. Maps the returned source_ids back to source_uuids
    4. Recovers any missing companies that were not included in the resolution

    Args:
        block: Dictionary containing block data with companies list
        baml_client: The BAML async client instance
        collector: Optional collector for BAML options
        iteration: Current iteration number for match_skip_history tracking

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
            if "uuid" in company and company["uuid"]:
                # Map the record's uuid into the source_uuids field so we can do a simple join on the edges
                if "source_uuids" not in company or not company["source_uuids"]:
                    company["source_uuids"] = [company["uuid"]]
                elif (
                    isinstance(company["source_uuids"], list)
                    and company["uuid"] not in company["source_uuids"]
                ):
                    company["source_uuids"].append(company["uuid"])

            # Single company blocks are not processed by BAML, so mark as skipped
            company["match_skip"] = False  # Not skipped, just single-company block
            # Preserve match_skip_history if it exists
            if "match_skip_history" not in company:
                company["match_skip_history"] = []

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

        # Track all input companies by their UUID for recovery
        input_companies_by_uuid: dict[str, dict[str, Any]] = {}

        # Build reverse index: source_uuid -> company that contains it
        source_uuid_to_company: dict[str, dict[str, Any]] = {}

        # Track which UUIDs went into the BAML call
        all_input_uuids: set[str] = set()

        # Convert companies to Company objects with integer IDs
        companies = []

        for comp_data in companies_data:
            # Store original company data for potential recovery
            if "uuid" in comp_data and comp_data["uuid"]:
                input_companies_by_uuid[comp_data["uuid"]] = comp_data
                all_input_uuids.add(comp_data["uuid"])

            # Build reverse index for source_uuids
            if "source_uuids" in comp_data and isinstance(comp_data["source_uuids"], list):
                for source_uuid in comp_data["source_uuids"]:
                    if source_uuid:
                        all_input_uuids.add(source_uuid)
                        # Map this source_uuid to the company that contains it
                        source_uuid_to_company[source_uuid] = comp_data

            # Deep copy to avoid modifying original data
            comp_copy = copy.deepcopy(comp_data)

            # Remove match_skip before sending to BAML
            if "match_skip" in comp_copy:
                del comp_copy["match_skip"]
            if "match_skip_history" in comp_copy:
                del comp_copy["match_skip_history"]

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

            # Handle ticker field - might be a dict or Row from parquet
            ticker_data = comp_copy.get("ticker")
            ticker = None
            if ticker_data:

                if isinstance(ticker_data, Row):
                    ticker_data = ticker_data.asDict()

                if isinstance(ticker_data, dict):
                    # If ticker is a dict, we need to validate the exchange field
                    exchange_value = ticker_data.get("exchange")
                    # Check if exchange is a valid Exchange enum value
                    valid_exchange = None
                    if exchange_value:
                        try:
                            # Try to convert to Exchange enum
                            if hasattr(Exchange, exchange_value):
                                valid_exchange = Exchange[exchange_value]
                            else:
                                # If not a valid enum, use UNK
                                valid_exchange = Exchange.UNK
                                logger.warning(
                                    f"Invalid exchange value '{exchange_value}' for company {comp_copy['name']}, using UNK"
                                )
                        except (KeyError, ValueError):
                            valid_exchange = Exchange.UNK
                            logger.warning(
                                f"Invalid exchange value '{exchange_value}' for company {comp_copy['name']}, using UNK"
                            )

                    # Create Ticker object with validated exchange
                    ticker = Ticker(
                        id=ticker_data.get("id"),
                        uuid=ticker_data.get("uuid"),
                        symbol=ticker_data.get("symbol", ""),
                        exchange=valid_exchange,
                    )
                else:
                    # If it's already a Ticker object, use it as is
                    ticker = ticker_data

            # Create Company object
            company = Company(
                id=comp_copy["id"],  # Use the integer ID
                uuid=None,  # Clear UUID for BAML
                name=comp_copy["name"],
                cik=comp_copy.get("cik"),
                ticker=ticker,  # Use the processed ticker
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
                match_skip=None,  # BAML should leave this unaltered
                match_skip_history=None,  # BAML should leave this unaltered
            )
            companies.append(company)

        # Create CompanyList and call BAML function
        company_list = CompanyList(
            block_key=block_key,
            block_key_type=block_key_type,
            block_size=len(companies),
            companies=companies,
        )

        # Setup few-show examples
        merge_companies_example_set: MergeCompanyExampleSet = company_dicts_to_baml(
            company_id_tracking_dicts
        )

        logger.debug(
            f"Submitting block '{block_key}' to MultiEntityResolution API with integer IDs"
        )

        # Call BAML with integer IDs
        if collector:
            baml_options = BamlCallOptions(collector=collector)
            result = await baml_client.FewShotMultiEntityResolution(
                company_list=company_list,
                merge_companies_example_set=merge_companies_example_set,
                baml_options=baml_options,
            )
        else:
            result = await baml_client.FewShotMultiEntityResolution(
                company_list=company_list, merge_companies_example_set=merge_companies_example_set
            )

        # Track which UUIDs appear in the BAML results
        output_uuids: set[str] = set()

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

            # Track all UUIDs that appear in the output
            if source_uuids_final:
                output_uuids.update(source_uuids_final)

            resolved_dict: dict[str, Any] = {
                "id": company.id,
                "uuid": company.uuid,
                "name": company.name,
                "cik": company.cik,
                "ticker": company.ticker.model_dump(mode="json") if company.ticker else None,
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
                "match_skip": False,  # This company was processed by BAML
                "match_skip_history": company.match_skip_history
                or [],  # Preserve history from BAML
            }

            resolved_companies.append(resolved_dict)

        # Find missing UUIDs - those that went in but didn't come out
        missing_uuids = all_input_uuids - output_uuids

        # Track which companies we need to recover entirely
        companies_to_recover: set[str] = set()

        # Track UUIDs we need to add back to existing output companies
        uuids_to_add_back: dict[str, list[str]] = {}  # company_uuid -> list of uuids to add

        if missing_uuids:
            # Count different types of missing UUIDs
            missing_primary_count = 0
            missing_source_count = 0

            for missing_uuid in missing_uuids:
                # Case 1: This UUID was a primary company UUID
                if missing_uuid in input_companies_by_uuid:
                    companies_to_recover.add(missing_uuid)
                    missing_primary_count += 1
                    logger.debug(
                        f"  Missing PRIMARY uuid: {missing_uuid} - will recover entire company"
                    )

                # Case 2: This UUID was in someone's source_uuids
                elif missing_uuid in source_uuid_to_company:
                    missing_source_count += 1
                    parent_company: dict[str, Any] = source_uuid_to_company[missing_uuid]
                    parent_uuid: Any | None = parent_company.get("uuid")

                    if parent_uuid:
                        # Check if the parent company is in the output
                        parent_in_output: bool = any(
                            parent_uuid in (comp.get("source_uuids") or [])
                            for comp in resolved_companies
                        )

                        if parent_in_output:
                            # Parent is in output, just need to ensure missing_uuid is in its source_uuids
                            logger.debug(
                                f"  Missing SOURCE uuid: {missing_uuid} from parent {parent_uuid} - will add to source_uuids"
                            )
                            if parent_uuid not in uuids_to_add_back:
                                uuids_to_add_back[parent_uuid] = []
                            uuids_to_add_back[parent_uuid].append(missing_uuid)
                        else:
                            # Parent company is also missing, need to recover it entirely
                            companies_to_recover.add(parent_uuid)
                            missing_primary_count += 1  # Parent is missing
                            logger.debug(
                                f"  Missing SOURCE uuid: {missing_uuid} but parent {parent_uuid} ALSO missing - will recover parent"
                            )

            # Log summary of missing UUIDs
            logger.warning(
                f"Block {block_key}: Found {len(missing_uuids)} missing UUIDs: "
                f"{missing_primary_count} primary, {missing_source_count} from source_uuids"
            )

        # Step 1: Add back missing UUIDs to existing output companies
        for resolved_company in resolved_companies:
            company_source_uuids: list[str] = resolved_company.get("source_uuids") or []  # type: ignore

            # Check if any of this company's source_uuids need additions
            for source_uuid in company_source_uuids:
                if source_uuid in uuids_to_add_back:
                    for uuid_to_add in uuids_to_add_back[source_uuid]:
                        if uuid_to_add not in company_source_uuids:
                            company_source_uuids.append(uuid_to_add)
                            logger.debug(f"Added {uuid_to_add} back to company's source_uuids")

            # Update the source_uuids
            if company_source_uuids:
                resolved_company["source_uuids"] = sorted(list(set(company_source_uuids)))  # type: ignore

        # Step 2: Recover entire companies that are missing
        recovered_count = 0
        for company_uuid in companies_to_recover:
            if company_uuid in input_companies_by_uuid:
                missing_company = copy.deepcopy(input_companies_by_uuid[company_uuid])

                # Ensure source_uuids contains the company's own UUID
                if "source_uuids" not in missing_company or not missing_company["source_uuids"]:
                    missing_company["source_uuids"] = [company_uuid]
                elif (
                    missing_company["source_uuids"] is not None
                    and company_uuid not in missing_company["source_uuids"]
                ):
                    missing_company["source_uuids"].append(company_uuid)

                # Mark as skipped in this iteration
                missing_company["match_skip"] = True
                # Companies in companies_to_recover are always primary UUIDs that went missing
                missing_company["match_skip_reason"] = "missing_in_match_output"

                # Update match_skip_history
                skip_history = missing_company.get("match_skip_history", [])
                # Ensure skip_history is a list (not None)
                if skip_history is None:
                    skip_history = []
                if iteration not in skip_history:
                    skip_history.append(iteration)
                missing_company["match_skip_history"] = skip_history

                resolved_companies.append(missing_company)
                recovered_count += 1

        if recovered_count > 0 or uuids_to_add_back:
            logger.info(
                f"Block {block_key}: Recovered {recovered_count} missing companies, "
                f"added back {sum(len(uuids) for uuids in uuids_to_add_back.values())} UUIDs"
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
        logger.error(f"Error processing block {block_key}: {e}", exc_info=True)
        # Return original companies unchanged on error, but keep them for recovery
        return {
            "block_key": block_key,
            "block_key_type": block_key_type,
            "original_companies": companies_data,  # Preserve for error recovery
            "resolved_companies": companies_data,
            "original_count": len(companies_data),
            "resolved_count": len(companies_data),
            "total_companies": len(companies_data),
            "was_resolved": False,
            "error": str(e),
        }

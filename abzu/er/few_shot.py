from typing import Any, Union

from abzu.baml_client.types import FewShotExample, MergeCompany, MergeCompanyExampleSet


def company_dicts_to_baml(
    merge_company_example_set_dict: dict[
        str,  # merge_companies
        list[  # MergeCompanyExampleSet.merge_companies
            dict[
                str,  # companies / merged_company
                Union[
                    list[dict[str, Union[int, list[int]]]],  # MergeCompany
                    dict[str, Union[int, list[int]]],  # MergeCompany
                ],  # This is also to format the line I hope
            ]  # This is also to format the line I hope
        ],  # This is to format the line I hope
    ],
) -> MergeCompanyExampleSet:
    """Convert a list of company dicts to a FewShotMergedCompanies object.

    Note that we do hard asserts, if the few-shot examples aren't complete, we want to die hard."""
    for few_shot_example in merge_company_example_set_dict["merge_companies"]:
        assert "merge_companies" in few_shot_example

        # Fill in the FewShotExample.companies field
        companies: list[MergeCompany] = []
        for company in few_shot_example["companies"]:
            assert "id" in company
            assert "source_ids" in company

            merge_company = MergeCompany(
                id=company["id"],  # type: ignore
                source_ids=company["source_ids"],  # type: ignore
            )
            companies.append(merge_company)

        # Fill in the FewShotExample.merged_company field
        assert "merged_company" in few_shot_example
        merged_company_dict = few_shot_example["merged_company"]
        assert "id" in merged_company_dict
        assert "source_ids" in merged_company_dict
        merged_company = MergeCompany(
            id=merged_company_dict["id"],  # type: ignore
            source_ids=merged_company_dict["source_ids"],  # type: ignore
        )

    merge_companies = [
        FewShotExample(
            companies=companies,
            merged_company=merged_company,
        )
    ]
    merge_company_example_set: MergeCompanyExampleSet = MergeCompanyExampleSet(
        merge_companies=merge_companies
    )

    return merge_company_example_set


company_id_tracking_dicts: dict[
    str, list[dict[str, Union[list[dict[str, Any]], dict[str, Any]]]]
] = {
    "merge_companies": [
        {
            "companies": [
                {"id": 1, "source_ids": [101, 102]},
                {"id": 2, "source_ids": [201, 202]},
            ],
            "merged_company": {"id": 10, "source_ids": [1, 2, 101, 102, 201, 202]},
        }
    ]
}
company_id_tracking_few_shot_candidates = company_dicts_to_baml(company_id_tracking_dicts)

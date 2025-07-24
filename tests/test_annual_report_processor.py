from typing import Any

from abzu.api.annual_report_processor import enrich_company_tickers


def test_enrich_company_tickers() -> None:
    data: dict[str, Any] = {
        "reporting_company": {"name": "Alpha Inc"},
        "suppliers": [
            {
                "customer_company": {"name": "Alpha Inc"},
                "supplier_company": {"name": "Beta Co"},
                "supplied_good_or_service": "widgets",
            }
        ],
        "partnerships": [{"company1": {"name": "Alpha Inc"}, "company2": {"name": "Gamma LLC"}}],
        "investments": [
            {
                "investor_company": {"name": "Alpha Inc"},
                "invested_company": {"name": "Delta Corp"},
                "investment_type": "acquisition",
            }
        ],
    }

    sec_map = {
        "alpha": "ALP",
        "beta": "BET",
        "gamma": "GAM",
        "delta": "DEL",
    }

    enrich_company_tickers(data, sec_map)

    assert data["reporting_company"]["ticker"]["symbol"] == "ALP"
    supplier = data["suppliers"][0]
    assert supplier["supplier_company"]["ticker"]["symbol"] == "BET"
    partnership = data["partnerships"][0]
    assert partnership["company2"]["ticker"]["symbol"] == "GAM"
    investment = data["investments"][0]
    assert investment["invested_company"]["ticker"]["symbol"] == "DEL"

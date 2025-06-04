// BAML Config for Extracting Company Relationships from Annual Reports

class AnnualReportData {
  reporting_company Company
  @description("The company that is the subject of the annual report.")

  fiscal_year int?
  @description("The fiscal year the report covers.")

  report_date string?
  @description("The date the report was filed or published, in ISO-8601 format.")

  subsidiaries Subsidiary[]?
  @description("Subsidiaries of the reporting company mentioned in the report.")

  partnerships AnnualReportPartnership[]?
  @description("Partnerships involving the reporting company mentioned in the report.")

  investments Investment[]?
  @description("Investments made by or in the reporting company mentioned in the report.")

  suppliers SupplierRelationship[]?
  @description("Supplier relationships of the reporting company mentioned in the report.")
}


class Subsidiary {
  name string
  @description("Formal name of the subsidiary.")

  parent_company Company
  @description("The parent company (usually the reporting_company).")

  jurisdiction_of_incorporation string?
  @description("State or country where the subsidiary is incorporated.")

  ownership_percentage float?
  @description("Percentage of ownership by the parent company, if stated.")
}

class AnnualReportPartnership {
  company1 Company
  @description("The reporting company or one of the primary companies in the partnership.")

  company2 Company
  @description("The other company in the partnership.")

  partnership_type string?
  @description("The nature or type of the partnership.")

  purpose string?
  @description("The stated purpose or goal of the partnership.")

  source_text_snippet string?
  @description("A snippet from the report describing the partnership.")
}

class Investment {
  investor_company Company?
  invested_company Company?
  investment_type DealType
  amount int?
  currency string?
  date string?
  purpose string?
  @description("Description of the investment or acquisition, including stake if mentioned.")
  source_text_snippet string?
  @description("A snippet from the report describing the investment or acquisition.")
}

class SupplierRelationship {
  customer_company Company
  supplier_company Company
  supplied_good_or_service string
  @description("The product, component, or service being supplied.")
  source_text_snippet string?
  @description("A snippet from the report describing the supplier relationship.")
}


function ExtractCompanyRelationshipsFromAnnualReport(report_text: string) -> AnnualReportData {
  client CustomGeminiFallback

  prompt #"
    Parse the following company annual report. Extract information related to subsidiaries, partnerships, investments (including acquisitions), and key suppliers of the reporting company.

    Annual Report Text:
    ---
    {{ report_text }}
    ---

    Important notes for supplier relationships:
    - customer_company: The company purchasing goods/services (usually the reporting company)
    - supplier_company: The company providing goods/services to the customer
    - For partnerships, ensure both companies are properly identified with complete company information
    - For investments, clearly distinguish between investor_company and invested_company

    {{ ctx.output_format }}

    JSON:
  "#
}


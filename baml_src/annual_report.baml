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

  partnerships Partnership[]?
  @description("Partnerships involving the reporting company mentioned in the report.")

  investments Investment[]?
  @description("Investments made by or in the reporting company mentioned in the report.")

  suppliers SupplierRelationship[]?
  @description("Supplier relationships of the reporting company mentioned in the report.")
}

class Company {
  name string
  @description("Formal name of the company, including legal suffix like Inc., Ltd., Co., etc. Normalize common variations.")

  ticker Ticker?
  @description("Ticker symbol of the company if publicly traded.")

  incorporation_jurisdiction string?
  @description("State or country of incorporation.")

  principal_executive_offices_location string?
  @description("Location of the company's principal executive offices.")
}

class Ticker {
  name string
  symbol string
  exchange string?
}

class Product {
  name string
  description string?
  manufacturer Company
}

class Technology {
  name string
  developer Company?
  description string?
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

class Partnership {
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

enum DealType {
  Sale @description("Sale of a product or technology")
  Acquisition @description("Acquisition of a company")
  Investment @description("Investment in a company or country")
}

function ExtractCompanyRelationshipsFromAnnualReport(report_text: string) -> AnnualReportData {
  client CustomGeminiFallback

  prompt #"
    Parse the following company annual report. Extract information related to subsidiaries, partnerships, investments (including acquisitions), and key suppliers of the reporting company.

    Annual Report Text:
    ---
    {{ report_text }}
    ---

    {{ ctx.output_format }}

    JSON:
  "#
}


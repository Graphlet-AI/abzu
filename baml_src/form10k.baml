// Form 10-K BAML schema for extracting structured data from SEC annual reports
// This schema is designed for investment thesis validation via Text2Cypher queries
// Reuses Company, Ticker, Exchange, Nation, Product, Technology from article.baml

// Import shared types from article.baml
// Company, Ticker, Exchange, Nation, Product, Technology, RelationshipType, Relationship

//
// ============================================================================
// ENUMERATIONS
// ============================================================================
//

enum RiskCategory {
  Strategic @description("Risks related to business strategy, competitive position, market conditions")
  Operational @description("Risks related to operations, supply chain, manufacturing, technology")
  Financial @description("Risks related to financial condition, liquidity, capital, debt, currency")
  Regulatory @description("Risks related to laws, regulations, compliance, government actions")
  Legal @description("Risks related to litigation, intellectual property, contracts")
  Cybersecurity @description("Risks related to data breaches, cyber attacks, IT systems")
  Environmental @description("Risks related to climate change, environmental regulations, sustainability")
  Macroeconomic @description("Risks related to economic conditions, inflation, interest rates, geopolitical events")
  Reputational @description("Risks related to brand, public perception, ESG concerns")
  TalentAndLabor @description("Risks related to workforce, key personnel, labor relations")
}

enum RiskSeverity {
  Critical @description("Could materially impair business viability")
  High @description("Could significantly impact financial performance")
  Medium @description("Could moderately affect operations or results")
  Low @description("Minimal expected impact")
}

enum CompetitivePosition {
  Leader @description("Dominant market position, leading market share")
  Challenger @description("Strong competitor actively pursuing market share")
  Follower @description("Established player following market trends")
  Niche @description("Specialized focus on specific market segment")
  Emerging @description("New entrant with growth potential")
}

enum SegmentType {
  Geographic @description("Region or country-based segment")
  ProductLine @description("Product or service category segment")
  CustomerType @description("Customer category segment (enterprise, consumer, government)")
  Channel @description("Distribution or sales channel segment")
}

enum GovernanceRating {
  Strong @description("Excellent governance practices")
  Adequate @description("Meets standard governance requirements")
  Weak @description("Governance concerns noted")
}

enum AuditOpinionType {
  Unqualified @description("Clean opinion, no material issues")
  Qualified @description("Opinion with specific exceptions")
  Adverse @description("Material misstatements exist")
  Disclaimer @description("Unable to express opinion")
}

enum ExecutiveRole {
  CEO @description("Chief Executive Officer")
  CFO @description("Chief Financial Officer")
  COO @description("Chief Operating Officer")
  CTO @description("Chief Technology Officer")
  CIO @description("Chief Information Officer")
  CISO @description("Chief Information Security Officer")
  CLO @description("Chief Legal Officer / General Counsel")
  CMO @description("Chief Marketing Officer")
  CHRO @description("Chief Human Resources Officer")
  President @description("President")
  Chairman @description("Chairman of the Board")
  ViceChairman @description("Vice Chairman")
  Director @description("Board Director")
  Other @description("Other executive position")
}

enum BoardCommittee {
  Audit @description("Audit Committee")
  Compensation @description("Compensation Committee")
  Nominating @description("Nominating and Governance Committee")
  Risk @description("Risk Committee")
  Technology @description("Technology Committee")
  ESG @description("Environmental, Social, Governance Committee")
  Finance @description("Finance Committee")
  Other @description("Other Committee")
}

enum AcquisitionType {
  Merger @description("Full merger of two companies")
  AssetPurchase @description("Purchase of specific assets")
  StockPurchase @description("Purchase of controlling shares")
  JointVenture @description("Formation of joint venture")
  StrategicInvestment @description("Minority investment")
  Spin @description("Spin-off or divestiture")
}

enum RevenueRecognitionBasis {
  PointInTime @description("Revenue recognized at a point in time")
  OverTime @description("Revenue recognized over time as performance obligations are satisfied")
  Subscription @description("Recurring subscription-based revenue")
  Usage @description("Usage-based or consumption-based revenue")
  Milestone @description("Milestone-based revenue recognition")
}

//
// ============================================================================
// ENTITY CLASSES
// ============================================================================
//

class Executive {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the executive is associated with.")

  name string
  @description("Full name of the executive")

  role ExecutiveRole
  @description("Primary role or title")

  title string?
  @description("Official title if different from role")

  age int?
  @description("Age of the executive")

  tenure_years int?
  @description("Years in current position")

  biography string?
  @description("Brief biography and relevant experience")

  total_compensation float?
  @description("Total compensation in USD")

  stock_ownership_shares int?
  @description("Number of shares owned")

  stock_ownership_percent float?
  @description("Percentage of outstanding shares owned")

  committees BoardCommittee[]?
  @description("Board committees served on")

  is_independent bool?
  @description("Whether the director is independent")
}

class RiskFactor {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the risk factor is associated with.")

  category RiskCategory
  @description("Category of risk")

  title string
  @description("Brief title or heading of the risk factor")

  description string
  @description("Detailed description of the risk")

  severity RiskSeverity?
  @description("Estimated severity of the risk")

  mitigation string?
  @description("Company's mitigation strategy if mentioned")

  related_companies int[]?
  @description("IDs of companies related to this risk (competitors, suppliers, etc.)")

  trend string?
  @description("Whether risk is increasing, decreasing, or stable")

  is_new bool?
  @description("Whether this is a newly disclosed risk factor")
}

class BusinessSegment {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the business segment is associated with.")

  name string
  @description("Name of the business segment")

  type SegmentType
  @description("Type of segment classification")

  description string
  @description("Description of segment operations")

  revenue float?
  @description("Segment revenue in USD")

  revenue_percent float?
  @description("Percentage of total revenue")

  operating_income float?
  @description("Segment operating income in USD")

  operating_margin float?
  @description("Operating margin percentage")

  assets float?
  @description("Segment assets in USD")

  growth_rate float?
  @description("Year-over-year revenue growth rate")

  key_products int[]?
  @description("IDs of key products in this segment")

  geographic_regions string[]?
  @description("Key geographic regions for this segment")
}

class GeographicMarket {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the geographic market is associated with.")

  region string
  @description("Region or country name")

  country Nation?
  @description("Country details if applicable")

  revenue float?
  @description("Revenue from this market in USD")

  revenue_percent float?
  @description("Percentage of total revenue")

  growth_rate float?
  @description("Year-over-year growth rate")

  employees int?
  @description("Number of employees in this region")

  key_facilities int?
  @description("Number of key facilities")

  regulatory_environment string?
  @description("Description of regulatory environment")

  competitive_position CompetitivePosition?
  @description("Company's competitive position in this market")
}

class Competitor {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the competitor is competing with.")

  competitor int
  @description("ID of the competitor company")

  segments int[]?
  @description("IDs of business segments where they compete")

  competitive_position CompetitivePosition?
  @description("Competitor's market position")

  threat_level string?
  @description("Assessment of competitive threat")

  key_differentiators string?
  @description("What differentiates the competitor")
}

class RevenueStream {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the revenue stream is associated with.")

  name string
  @description("Name of the revenue stream")

  description string
  @description("Description of the revenue source")

  recognition_basis RevenueRecognitionBasis
  @description("How revenue is recognized")

  revenue float?
  @description("Revenue amount in USD")

  revenue_percent float?
  @description("Percentage of total revenue")

  growth_rate float?
  @description("Year-over-year growth rate")

  is_recurring bool?
  @description("Whether revenue is recurring")

  deferred_revenue float?
  @description("Deferred revenue balance in USD")
}

class FinancialMetric {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the financial metric is associated with.")

  metric_name string
  @description("Name of the metric")

  value float
  @description("Value of the metric")

  unit string?
  @description("Unit of measurement (USD, percent, ratio, etc.)")

  period string
  @description("Fiscal period (e.g., FY2024, Q4 2024)")

  year_over_year_change float?
  @description("Percentage change from prior year")

  description string?
  @description("Context or notes about the metric")
}

class GuidanceMetric {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the guidance metric is associated with.")

  metric_name string
  @description("Name of the guidance metric")

  low_estimate float?
  @description("Low end of guidance range")

  high_estimate float?
  @description("High end of guidance range")

  point_estimate float?
  @description("Point estimate if no range given")

  unit string?
  @description("Unit of measurement")

  period string
  @description("Period for guidance (e.g., FY2025, Q1 2025)")

  prior_guidance_low float?
  @description("Prior low guidance if revised")

  prior_guidance_high float?
  @description("Prior high guidance if revised")

  assumptions string?
  @description("Key assumptions underlying guidance")
}

class GovernanceItem {
  id int
  @description("Unique identifier")

  company int
  @description("Company id the governance item is associated with.")

  item_type string
  @description("Type: audit_fee, related_party_transaction, shareholder_proposal, etc.")

  description string
  @description("Description of the governance item")

  amount float?
  @description("Amount if applicable in USD")

  parties_involved int[]?
  @description("IDs of related parties")

  outcome string?
  @description("Outcome or resolution")
}

//
// ============================================================================
// TOP-LEVEL FORM 10-K CLASS
// ============================================================================
//

class Form10K {
  // Document metadata
  fiscal_year int
  @description("Fiscal year of the report")

  fiscal_year_end string
  @description("Fiscal year end date in ISO-8601 format")

  filing_date string?
  @description("SEC filing date in ISO-8601 format")

  cik string?
  @description("SEC Central Index Key")

  accession_number string?
  @description("SEC accession number")

  // Filer company - the company this 10-K is about
  filer Company
  @description("The company filing this 10-K")

  // Part I - Business
  business_description string
  @description("Description of the company's business operations")

  industry string?
  @description("Primary industry classification")

  sic_code string?
  @description("Standard Industrial Classification code")

  naics_code string?
  @description("North American Industry Classification System code")

  employees int?
  @description("Total number of employees")

  business_segments BusinessSegment[]?
  @description("Operating segments")

  geographic_markets GeographicMarket[]?
  @description("Geographic market breakdown")

  products Product[]?
  @description("Key products and services")

  technologies Technology[]?
  @description("Key technologies")

  revenue_streams RevenueStream[]?
  @description("Revenue stream breakdown")

  // Companies - all companies mentioned in the filing
  companies Company[]
  @description("All companies mentioned in the filing")

  // Competition
  competitors Competitor[]?
  @description("Key competitors")

  competitive_strengths string[]?
  @description("Company's competitive strengths")

  competitive_weaknesses string[]?
  @description("Company's competitive weaknesses")

  barriers_to_entry string[]?
  @description("Industry barriers to entry")

  // Risk Factors (Part I, Item 1A)
  risk_factors RiskFactor[]
  @description("Risk factors disclosed in the filing")

  // Properties (Part I, Item 2)
  properties_description string?
  @description("Description of material properties")

  facilities_count int?
  @description("Number of significant facilities")

  owned_square_feet int?
  @description("Total owned property in square feet")

  leased_square_feet int?
  @description("Total leased property in square feet")

  // Part II - Financial Information
  // Key financial metrics
  total_revenue float?
  @description("Total revenue in USD")

  revenue_growth float?
  @description("Revenue growth rate percentage")

  gross_profit float?
  @description("Gross profit in USD")

  gross_margin float?
  @description("Gross margin percentage")

  operating_income float?
  @description("Operating income in USD")

  operating_margin float?
  @description("Operating margin percentage")

  net_income float?
  @description("Net income in USD")

  net_margin float?
  @description("Net margin percentage")

  eps_basic float?
  @description("Basic earnings per share")

  eps_diluted float?
  @description("Diluted earnings per share")

  total_assets float?
  @description("Total assets in USD")

  total_liabilities float?
  @description("Total liabilities in USD")

  stockholders_equity float?
  @description("Total stockholders' equity in USD")

  cash_and_equivalents float?
  @description("Cash and cash equivalents in USD")

  total_debt float?
  @description("Total debt in USD")

  free_cash_flow float?
  @description("Free cash flow in USD")

  capex float?
  @description("Capital expenditures in USD")

  rd_expense float?
  @description("Research and development expense in USD")

  rd_percent_of_revenue float?
  @description("R&D as percentage of revenue")

  // Additional financial metrics
  financial_metrics FinancialMetric[]?
  @description("Additional financial metrics")

  // Forward guidance
  guidance_metrics GuidanceMetric[]?
  @description("Forward-looking guidance")

  // Part III - Directors and Officers
  executives Executive[]?
  @description("Executive officers")

  board_members Executive[]?
  @description("Board of Directors")

  audit_committee_financial_expert string?
  @description("Name of audit committee financial expert")

  code_of_ethics_url string?
  @description("URL to code of ethics")

  // Corporate governance
  governance_items GovernanceItem[]?
  @description("Corporate governance matters")

  audit_fees float?
  @description("Audit fees paid in USD")

  audit_opinion AuditOpinionType?
  @description("Type of audit opinion received")

  material_weakness bool?
  @description("Whether material weakness in internal controls exists")

  // Part IV - Exhibits and Schedules
  intellectual_property Technology[]?
  @description("Key intellectual property")

  // Relationships
  customers Company[]?
  @description("Key customers")

  suppliers Company[]?
  @description("Key suppliers")

  relationships Relationship[]?
  @description("All inter-company relationships")

  // Regulatory matters
  regulatory_bodies string[]?
  @description("Key regulatory bodies overseeing the company")

  pending_regulatory_matters string[]?
  @description("Pending regulatory approvals or investigations")

  // ESG and sustainability
  environmental_initiatives string[]?
  @description("Environmental initiatives mentioned")

  social_initiatives string[]?
  @description("Social responsibility initiatives")

  governance_highlights string[]?
  @description("Governance highlights")

  // MD&A highlights
  mda_summary string?
  @description("Summary of Management Discussion and Analysis")

  key_trends string[]?
  @description("Key business trends identified")

  key_uncertainties string[]?
  @description("Key uncertainties or challenges")

  // Ensure referential integrity for relationships
  @@assert(referential_integrity, {{
    this.relationships is none or (
    this.relationships|map(attribute='src_company')|
    select('in', this.companies|map(attribute='id'))|list|length ==
    this.relationships|length and
    this.relationships|map(attribute='dst_company')|
    select('in', this.companies|map(attribute='id'))|list|length ==
    this.relationships|length)
  }})
}

//
// ============================================================================
// EXTRACTION FUNCTION
// ============================================================================
//

function ExtractForm10K(filing_text: string) -> Form10K {
  client Gemini20Flash

  prompt #"
    You are an expert financial analyst extracting structured data from SEC Form 10-K filings.
    Parse the following 10-K filing and extract comprehensive structured information for investment analysis.

    IMPORTANT GUIDELINES:
    1. Extract ALL companies mentioned - competitors, customers, suppliers, partners, subsidiaries
    2. Assign unique integer IDs to all entities (companies, products, technologies, etc.)
    3. Create relationships between companies whenever the filing describes their interactions
    4. Be thorough with risk factors - investors rely on complete risk disclosure
    5. Extract financial metrics with their exact values and periods
    6. Identify forward-looking guidance carefully
    7. For relationships, always specify both source and destination company IDs
    8. Skip fields that would be null unless they are required

    The filer company (the company this 10-K is about) should always have ID = 1.

    {# Output format instructions #}
    {{ ctx.output_format(hoist_classes=[
      "Company", "Ticker", "Product", "Technology", "Executive", "RiskFactor",
      "BusinessSegment", "GeographicMarket","RevenueStream",
      "FinancialMetric", "GuidanceMetric", "GovernanceItem",
      "Relationship"
    ]) }}

    {{ _.role("user") }}
    {{ filing_text }}
  "#
}

//
// ============================================================================
// TEST CASE
// ============================================================================
//

test GoogleForm10KTest {
  functions [ExtractForm10K]
  args {
    filing_text #"
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Form 10-K
ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934
For the fiscal year ended December 31, 2024
Commission File Number: 001-37580

ALPHABET INC.
1600 Amphitheatre Parkway
Mountain View, CA 94043

PART I

Item 1. Business

Alphabet Inc. is a holding company that provides products and platforms in various industries globally. We were incorporated in Delaware on October 2, 2015. Our portfolio of products and services includes Google Search, YouTube, Google Cloud, Android, Google Play, and Waymo.

Our revenues are primarily generated from advertising on Google Search, YouTube, and the Google Display Network. Google Cloud provides enterprise cloud computing services. Other Bets includes Waymo (autonomous driving), Verily (life sciences), and other emerging businesses.

Competition: We face significant competition from Microsoft Corporation, Amazon.com, Inc., Apple Inc., Meta Platforms, Inc., and other technology companies. In cloud computing, we compete with Amazon Web Services and Microsoft Azure. In digital advertising, we compete with Meta, Amazon, and Microsoft.

Item 1A. Risk Factors

We face intense competition in all of our businesses. If we do not continue to innovate and provide products and services that are useful to users, we may not remain competitive.

Our revenues depend on advertising. Changes in online advertising markets, including from increased use of AI and ad-blocking technologies, could adversely affect our advertising revenues.

We are subject to regulatory investigations and legal proceedings. The Department of Justice and various state attorneys general have filed antitrust lawsuits against us.

Cybersecurity threats could disrupt our services. We process large amounts of user data, making us a target for cyberattacks.

PART II

Item 8. Financial Statements

Total revenues: $350,018 million (2024), $307,394 million (2023)
Operating income: $94,500 million (2024), $84,293 million (2023)
Net income: $80,000 million (2024), $73,795 million (2023)
Total assets: $432,000 million
Total debt: $28,000 million
Cash and equivalents: $95,000 million
R&D expense: $45,000 million
Employees: 182,000

PART III

Item 10. Directors, Executive Officers and Corporate Governance

Sundar Pichai - Chief Executive Officer, age 52
Ruth Porat - President and Chief Investment Officer, age 66
John Hennessy - Chairman of the Board
"#
  }
}

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, default=1)

    # FICA
    ss_rate = Column(Float, default=0.062)
    medicare_rate = Column(Float, default=0.0145)
    ss_wage_base = Column(Float, default=176100)

    # FUTA
    futa_rate = Column(Float, default=0.006)
    futa_wage_base = Column(Float, default=7000)

    # WC factors
    fixed_cost_factor = Column(Float, default=0.39)
    loss_fund_factor = Column(Float, default=0.5)
    combined_cost_factor = Column(Float, default=0.89)
    pte_weight = Column(Float, default=0.75)

    # WC state lists (comma-separated)
    monopolistic_states = Column(String, default="WA,WY,ND,OH")
    mcp_states = Column(String, default="RI,NY,NJ,PA,LA,WI,MN,SD,KS,MT,AZ,UT,NV,CA,OR")

    # Pay periods JSON: {"weekly":52,"biweekly":26,"semimonthly":24,"monthly":12}
    pay_periods_json = Column(Text, default='{"weekly":52,"biweekly":26,"semimonthly":24,"monthly":12}')

    # Sunz carrier charge — currently 0 in practice, reserved
    wc_policy_adjustment = Column(Float, default=0.0)

    futa_approach = Column(String, default="B")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="draft")  # draft | in_review | approved

    # General Information
    consultant_name = Column(String)
    date = Column(String)
    legal_name = Column(String)
    dba = Column(String)
    main_address = Column(String)
    city = Column(String)
    state = Column(String)
    zip = Column(String)
    fein = Column(String)
    website = Column(String)
    org_structure = Column(String)
    naics = Column(String)
    sic = Column(String)
    years_in_business = Column(Integer)
    num_locations = Column(Integer)
    main_phone = Column(String)
    owner_name = Column(String)
    owner_phone = Column(String)
    owner_email = Column(String)
    owner_cell = Column(String)
    contact_name = Column(String)
    contact_phone = Column(String)
    contact_cell = Column(String)
    contact_email = Column(String)
    states_operating = Column(Text)  # JSON array as text
    description_of_operations = Column(Text)

    # Compliance Questionnaire
    eeoc_violations = Column(Boolean, default=False)
    eeoc_explanation = Column(Text)
    active_claims = Column(Boolean, default=False)
    active_claims_explanation = Column(Text)
    cobra_continuation = Column(Boolean, default=False)
    cobra_explanation = Column(Text)
    past_layoffs = Column(Boolean, default=False)
    past_layoffs_explanation = Column(Text)
    future_layoffs = Column(Boolean, default=False)
    future_layoffs_explanation = Column(Text)
    leave_of_absence = Column(Boolean, default=False)
    leave_explanation = Column(Text)

    # Medical Questionnaire
    medical_carve_out = Column(Boolean, default=False)
    enrolled_over_50 = Column(Boolean, default=False)
    enrolled_under_10 = Column(Boolean, default=False)
    level_funded_plan = Column(Boolean, default=False)
    currently_has_health_insurance = Column(Boolean, default=False)
    census_available = Column(Boolean, default=False)
    cobra_expected = Column(Boolean, default=False)

    # Ancillary Benefits
    offers_ancillary_benefits = Column(Boolean, default=False)
    wants_ancillary_benefits = Column(Boolean, default=False)
    current_contribution_strategy = Column(Text)
    new_contribution_strategy = Column(Text)

    # Payroll
    payroll_frequency = Column(String)  # weekly | biweekly | semimonthly | monthly
    pay_cycle_start = Column(String)
    pay_cycle_end = Column(String)
    pay_date = Column(String)

    # Workers' Compensation
    wc_carve_out = Column(Boolean, default=False)
    proposed_mod = Column(Float, default=1.0)
    shared_claim_fee = Column(Float, default=0.0)
    min_wc_fee_per_week = Column(Float, default=0.0)

    # WC Losses header fields
    new_company = Column(Boolean, default=False)
    gaps_in_coverage = Column(Boolean, default=False)

    # Final Pricing
    admin_method = Column(Integer, default=1)  # 1 | 2 | 3
    admin_rate = Column(Float, default=0.0)

    # Commission
    internal_commission_pct = Column(Float, default=0.0)
    external_commission_pct = Column(Float, default=0.0)
    broker_wc_commission_pct = Column(Float, default=0.0)

    # Ancillary fees
    implementation_fee = Column(Float, default=0.0)
    epli_fee = Column(Float, default=0.0)
    include_tlm = Column(Boolean, default=False)
    include_epli = Column(Boolean, default=False)

    # FUTA turnover input
    w2s_generated = Column(Float, default=0.0)


class WCLine(Base):
    __tablename__ = "wc_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    state = Column(String)
    wc_code = Column(String)
    annual_gw = Column(Float, default=0.0)
    ftes = Column(Float, default=0.0)
    ptes = Column(Float, default=0.0)
    current_client_rate = Column(Float, default=0.0)
    # Manual rate from WC Rates table — stored at intake since full WC Rates table not yet imported
    manual_rate = Column(Float, default=0.0)


class SutaLine(Base):
    __tablename__ = "suta_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    state = Column(String)
    gws = Column(Float, default=0.0)
    total_wses = Column(Float, default=0.0)
    current_client_rate = Column(Float, default=0.0)
    billing_rate = Column(Float, default=0.0)
    cost_rate = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
    turnover_pct = Column(Float, default=0.10)


class SutaRate(Base):
    __tablename__ = "suta_rates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String, unique=True, nullable=False)
    threshold = Column(Float)
    vhr_min_rate = Column(Float)
    client_reporting = Column(Boolean, default=False)
    our_cost = Column(Float)


class WCLoss(Base):
    __tablename__ = "wc_losses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    coverage_period_start = Column(String)
    coverage_period_end = Column(String)
    total_losses_incurred = Column(Float, default=0.0)
    num_claims = Column(Integer, default=0)
    months_in_policy = Column(Integer, default=0)
    open_claims = Column(Integer, default=0)

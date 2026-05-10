from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from database import Base


class Contact(Base):
    __tablename__ = "contacts"

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
    locations = Column(Text)         # JSON array: [{address, employees}]
    description_of_operations = Column(Text)
    consultant_name_split = Column(String)
    referral_partner_business = Column(String)
    referral_partner_name = Column(String)
    county = Column(String)

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
    effective_date = Column(String)
    method_of_payment = Column(String)
    requested_payroll_delivery = Column(String)

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
    admin_rate = Column(Float, default=0.0)          # method 1 vested
    admin_rate_2 = Column(Float, default=0.0)        # method 2 vested
    admin_rate_3 = Column(Float, default=0.0)        # method 3 vested
    current_admin_rate = Column(Float, default=0.0)  # method 1 current
    current_admin_rate_2 = Column(Float, default=0.0)
    current_admin_rate_3 = Column(Float, default=0.0)

    # Commission
    internal_commission_pct = Column(Float, default=0.0)
    external_commission_pct = Column(Float, default=0.0)
    broker_wc_commission_pct = Column(Float, default=0.0)

    # Ancillary fees
    implementation_fee = Column(Float, default=0.0)
    epli_rate = Column(Float, default=0.0)
    include_epli = Column(Boolean, default=False)

    # FUTA turnover input (decimal; can exceed 1.0 when W-2s > avg headcount)
    futa_turnover_rate = Column(Float, default=0.1)

    # UI state — JSON dict of card-id → locked boolean
    card_lock_states = Column(Text, nullable=True)

    # Admin Fee
    offered_promotion = Column(Text, nullable=True)

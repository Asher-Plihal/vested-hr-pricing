"""
Defines the shape of client data at each stage of its lifecycle. ClientCreate is the
minimal payload to open a new client (just a name). ClientListItem is the condensed
version shown in the dashboard table. ClientUpdate is the full form payload sent on
every save — all fields are optional and it includes the WC lines, SUTA lines, and loss
history as nested lists. ClientOut is the full record returned when loading a client,
with all sub-lines resolved and included.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from schemas.workers_comp import WCLineIn, WCLineOut, WCLossIn, WCLossOut
from schemas.taxes import SutaLineIn, SutaLineOut


class ClientCreate(BaseModel):
    legal_name: Optional[str] = None
    consultant_name: Optional[str] = None


class ClientListItem(BaseModel):
    id: int
    legal_name: Optional[str]
    consultant_name: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = {"from_attributes": True}


class ClientUpdate(BaseModel):
    status: Optional[str] = None
    consultant_name: Optional[str] = None
    date: Optional[str] = None
    legal_name: Optional[str] = None
    dba: Optional[str] = None
    main_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    fein: Optional[str] = None
    website: Optional[str] = None
    org_structure: Optional[str] = None
    naics: Optional[str] = None
    sic: Optional[str] = None
    years_in_business: Optional[int] = None
    num_locations: Optional[int] = None
    main_phone: Optional[str] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    owner_cell: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_cell: Optional[str] = None
    contact_email: Optional[str] = None
    states_operating: Optional[str] = None
    locations: Optional[str] = None
    description_of_operations: Optional[str] = None
    consultant_name_split: Optional[str] = None
    referral_partner_business: Optional[str] = None
    referral_partner_name: Optional[str] = None
    county: Optional[str] = None
    eeoc_violations: Optional[bool] = None
    eeoc_explanation: Optional[str] = None
    active_claims: Optional[bool] = None
    active_claims_explanation: Optional[str] = None
    cobra_continuation: Optional[bool] = None
    cobra_explanation: Optional[str] = None
    past_layoffs: Optional[bool] = None
    past_layoffs_explanation: Optional[str] = None
    future_layoffs: Optional[bool] = None
    future_layoffs_explanation: Optional[str] = None
    leave_of_absence: Optional[bool] = None
    leave_explanation: Optional[str] = None
    medical_carve_out: Optional[bool] = None
    enrolled_over_50: Optional[bool] = None
    enrolled_under_10: Optional[bool] = None
    level_funded_plan: Optional[bool] = None
    currently_has_health_insurance: Optional[bool] = None
    census_available: Optional[bool] = None
    cobra_expected: Optional[bool] = None
    offers_ancillary_benefits: Optional[bool] = None
    wants_ancillary_benefits: Optional[bool] = None
    current_contribution_strategy: Optional[str] = None
    new_contribution_strategy: Optional[str] = None
    payroll_frequency: Optional[str] = None
    pay_cycle_start: Optional[str] = None
    pay_cycle_end: Optional[str] = None
    pay_date: Optional[str] = None
    effective_date: Optional[str] = None
    method_of_payment: Optional[str] = None
    requested_payroll_delivery: Optional[str] = None
    wc_carve_out: Optional[bool] = None
    proposed_mod: Optional[float] = None
    shared_claim_fee: Optional[float] = None
    min_wc_fee_per_week: Optional[float] = None
    new_company: Optional[bool] = None
    gaps_in_coverage: Optional[bool] = None
    admin_method: Optional[int] = None
    admin_rate: Optional[float] = None
    admin_rate_2: Optional[float] = None
    admin_rate_3: Optional[float] = None
    current_admin_rate: Optional[float] = None
    current_admin_rate_2: Optional[float] = None
    current_admin_rate_3: Optional[float] = None
    internal_commission_pct: Optional[float] = None
    external_commission_pct: Optional[float] = None
    broker_wc_commission_pct: Optional[float] = None
    implementation_fee: Optional[float] = None
    epli_rate: Optional[float] = None
    include_epli: Optional[bool] = None
    futa_turnover_rate: Optional[float] = None
    card_lock_states: Optional[str] = None
    wc_lines: Optional[list[WCLineIn]] = None
    suta_lines: Optional[list[SutaLineIn]] = None
    wc_losses: Optional[list[WCLossIn]] = None


class ClientOut(BaseModel):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    status: Optional[str]
    consultant_name: Optional[str]
    date: Optional[str]
    legal_name: Optional[str]
    dba: Optional[str]
    main_address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    fein: Optional[str]
    website: Optional[str]
    org_structure: Optional[str]
    naics: Optional[str]
    sic: Optional[str]
    years_in_business: Optional[int]
    num_locations: Optional[int]
    main_phone: Optional[str]
    owner_name: Optional[str]
    owner_phone: Optional[str]
    owner_email: Optional[str]
    owner_cell: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    contact_cell: Optional[str]
    contact_email: Optional[str]
    states_operating: Optional[str]
    locations: Optional[str]
    description_of_operations: Optional[str]
    consultant_name_split: Optional[str]
    referral_partner_business: Optional[str]
    referral_partner_name: Optional[str]
    county: Optional[str]
    eeoc_violations: Optional[bool]
    eeoc_explanation: Optional[str]
    active_claims: Optional[bool]
    active_claims_explanation: Optional[str]
    cobra_continuation: Optional[bool]
    cobra_explanation: Optional[str]
    past_layoffs: Optional[bool]
    past_layoffs_explanation: Optional[str]
    future_layoffs: Optional[bool]
    future_layoffs_explanation: Optional[str]
    leave_of_absence: Optional[bool]
    leave_explanation: Optional[str]
    medical_carve_out: Optional[bool]
    enrolled_over_50: Optional[bool]
    enrolled_under_10: Optional[bool]
    level_funded_plan: Optional[bool]
    currently_has_health_insurance: Optional[bool]
    census_available: Optional[bool]
    cobra_expected: Optional[bool]
    offers_ancillary_benefits: Optional[bool]
    wants_ancillary_benefits: Optional[bool]
    current_contribution_strategy: Optional[str]
    new_contribution_strategy: Optional[str]
    payroll_frequency: Optional[str]
    pay_cycle_start: Optional[str]
    pay_cycle_end: Optional[str]
    pay_date: Optional[str]
    effective_date: Optional[str]
    method_of_payment: Optional[str]
    requested_payroll_delivery: Optional[str]
    wc_carve_out: Optional[bool]
    proposed_mod: Optional[float]
    shared_claim_fee: Optional[float]
    min_wc_fee_per_week: Optional[float]
    new_company: Optional[bool]
    gaps_in_coverage: Optional[bool]
    admin_method: Optional[int]
    admin_rate: Optional[float]
    admin_rate_2: Optional[float]
    admin_rate_3: Optional[float]
    current_admin_rate: Optional[float]
    current_admin_rate_2: Optional[float]
    current_admin_rate_3: Optional[float]
    internal_commission_pct: Optional[float]
    external_commission_pct: Optional[float]
    broker_wc_commission_pct: Optional[float]
    implementation_fee: Optional[float]
    epli_rate: Optional[float]
    include_epli: Optional[bool]
    futa_turnover_rate: Optional[float]
    card_lock_states: Optional[str] = None
    wc_lines: list[WCLineOut] = []
    suta_lines: list[SutaLineOut] = []
    wc_losses: list[WCLossOut] = []
    model_config = {"from_attributes": True}

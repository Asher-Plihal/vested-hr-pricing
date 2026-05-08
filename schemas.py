from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


# ── SystemConfig ──────────────────────────────────────────────────────────────

class SystemConfigOut(BaseModel):
    id: int
    ss_rate: float
    medicare_rate: float
    ss_wage_base: float
    futa_rate: float
    futa_wage_base: float
    fixed_cost_factor: float
    loss_fund_factor: float
    combined_cost_factor: float
    pte_weight: float
    monopolistic_states: str
    mcp_states: str
    pay_periods_json: str
    wc_policy_adjustment: float
    futa_approach: str

    model_config = {"from_attributes": True}


class SystemConfigUpdate(BaseModel):
    ss_rate: Optional[float] = None
    medicare_rate: Optional[float] = None
    ss_wage_base: Optional[float] = None
    futa_rate: Optional[float] = None
    futa_wage_base: Optional[float] = None
    fixed_cost_factor: Optional[float] = None
    loss_fund_factor: Optional[float] = None
    combined_cost_factor: Optional[float] = None
    pte_weight: Optional[float] = None
    monopolistic_states: Optional[str] = None
    mcp_states: Optional[str] = None
    pay_periods_json: Optional[str] = None
    wc_policy_adjustment: Optional[float] = None
    futa_approach: Optional[str] = None


# ── Sub-models ────────────────────────────────────────────────────────────────

class WCLineIn(BaseModel):
    state: Optional[str] = None
    wc_code: Optional[str] = None
    annual_gw: float = 0.0
    ftes: float = 0.0
    ptes: float = 0.0
    current_client_rate: float = 0.0
    manual_rate: float = 0.0


class WCLineOut(WCLineIn):
    id: int
    client_id: int
    model_config = {"from_attributes": True}


class SutaLineIn(BaseModel):
    state: Optional[str] = None
    gws: float = 0.0
    total_wses: float = 0.0
    current_client_rate: float = 0.0
    billing_rate: float = 0.0
    cost_rate: float = 0.0
    threshold: float = 0.0
    turnover_pct: float = 0.10


class SutaLineOut(SutaLineIn):
    id: int
    client_id: int
    model_config = {"from_attributes": True}


class WCLossIn(BaseModel):
    coverage_period_start: Optional[str] = None
    coverage_period_end: Optional[str] = None
    total_losses_incurred: float = 0.0
    num_claims: int = 0
    months_in_policy: int = 0
    open_claims: int = 0


class WCLossOut(WCLossIn):
    id: int
    client_id: int
    model_config = {"from_attributes": True}


# ── Client ────────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    legal_name: Optional[str] = None
    consultant_name: Optional[str] = None


class ClientListItem(BaseModel):
    id: int
    legal_name: Optional[str]
    consultant_name: Optional[str]
    status: Optional[str]
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
    description_of_operations: Optional[str] = None
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
    wc_carve_out: Optional[bool] = None
    proposed_mod: Optional[float] = None
    shared_claim_fee: Optional[float] = None
    min_wc_fee_per_week: Optional[float] = None
    new_company: Optional[bool] = None
    gaps_in_coverage: Optional[bool] = None
    admin_method: Optional[int] = None
    admin_rate: Optional[float] = None
    internal_commission_pct: Optional[float] = None
    external_commission_pct: Optional[float] = None
    broker_wc_commission_pct: Optional[float] = None
    implementation_fee: Optional[float] = None
    epli_fee: Optional[float] = None
    include_tlm: Optional[bool] = None
    include_epli: Optional[bool] = None
    w2s_generated: Optional[float] = None
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
    description_of_operations: Optional[str]
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
    wc_carve_out: Optional[bool]
    proposed_mod: Optional[float]
    shared_claim_fee: Optional[float]
    min_wc_fee_per_week: Optional[float]
    new_company: Optional[bool]
    gaps_in_coverage: Optional[bool]
    admin_method: Optional[int]
    admin_rate: Optional[float]
    internal_commission_pct: Optional[float]
    external_commission_pct: Optional[float]
    broker_wc_commission_pct: Optional[float]
    implementation_fee: Optional[float]
    epli_fee: Optional[float]
    include_tlm: Optional[bool]
    include_epli: Optional[bool]
    w2s_generated: Optional[float]
    wc_lines: list[WCLineOut] = []
    suta_lines: list[SutaLineOut] = []
    wc_losses: list[WCLossOut] = []
    model_config = {"from_attributes": True}


# ── Calculate ─────────────────────────────────────────────────────────────────

class CalculateRequest(BaseModel):
    client: ClientUpdate
    wc_lines: list[WCLineIn] = []
    suta_lines: list[SutaLineIn] = []
    ancillary: Optional[dict[str, Any]] = None

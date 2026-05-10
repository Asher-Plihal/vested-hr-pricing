"""
Defines the shape of data going in and out of the config endpoints. SystemConfigOut is
what the API returns when the config page loads — all current settings. SystemConfigUpdate
is what the config page sends when a field changes — every field is optional so only the
changed value needs to be included.
"""
from typing import Optional
from pydantic import BaseModel


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
    independent_bureau_states: str
    pay_periods_json: str
    wc_policy_adjustment: float
    consultant_commission_upfront: float
    consultant_commission_ongoing: float
    admin_commission_pool_pct: float
    consultant_min_ongoing_pct: float
    futa_approach: str
    fee_min_admin_per_cycle: float
    fee_delivery_min: float
    fee_delivery_max: float
    fee_out_of_cycle_payroll: float
    fee_returned_check: float
    fee_timekeeping_implementation: float
    fee_timekeeping_monthly_per_ee: float
    fee_applicant_tracking_implementation: float
    fee_online_lms_implementation: float
    fee_online_lms_per_ee_monthly: float
    fee_mvr_report: float
    fee_everify_per_ee: float
    fee_wc_waiver_subrogation: float
    fee_wc_late_reporting: float
    fee_wc_alternate_employer_endorsement: float
    fee_reactivation: float
    fee_late_payroll_submission: float
    tlm_rate: float
    wire_ach_rate: float

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
    independent_bureau_states: Optional[str] = None
    pay_periods_json: Optional[str] = None
    wc_policy_adjustment: Optional[float] = None
    consultant_commission_upfront: Optional[float] = None
    consultant_commission_ongoing: Optional[float] = None
    admin_commission_pool_pct: Optional[float] = None
    consultant_min_ongoing_pct: Optional[float] = None
    futa_approach: Optional[str] = None
    fee_min_admin_per_cycle: Optional[float] = None
    fee_delivery_min: Optional[float] = None
    fee_delivery_max: Optional[float] = None
    fee_out_of_cycle_payroll: Optional[float] = None
    fee_returned_check: Optional[float] = None
    fee_timekeeping_implementation: Optional[float] = None
    fee_timekeeping_monthly_per_ee: Optional[float] = None
    fee_applicant_tracking_implementation: Optional[float] = None
    fee_online_lms_implementation: Optional[float] = None
    fee_online_lms_per_ee_monthly: Optional[float] = None
    fee_mvr_report: Optional[float] = None
    fee_everify_per_ee: Optional[float] = None
    fee_wc_waiver_subrogation: Optional[float] = None
    fee_wc_late_reporting: Optional[float] = None
    fee_wc_alternate_employer_endorsement: Optional[float] = None
    fee_reactivation: Optional[float] = None
    fee_late_payroll_submission: Optional[float] = None
    tlm_rate: Optional[float] = None
    wire_ach_rate: Optional[float] = None

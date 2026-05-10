"""
The main pricing engine endpoint. The client form sends its current state here every
time a field changes, and this returns the full deal summary — WC billing, taxes, admin
fee, commissions, and profit/loss — without saving anything to the database. It pulls
system config from the DB, then runs the client data through the full calc/ pipeline
in order: workers comp → FICA → FUTA → SUTA → admin fee → commission → summary.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SystemConfig
from schemas import CalculateRequest

from calc.workers_comp import calculate_wc
from calc.taxes import calculate_fica, calculate_futa, calculate_suta
from calc.admin import calculate_admin
from calc.commission import calculate_commission
from calc.proposal import build_proposal
from calc.summary import build_analysis

router = APIRouter(prefix="/calculate", tags=["calculate"])


@router.post("")
def run_calculate(body: CalculateRequest, db: Session = Depends(get_db)):
    cfg_row = db.query(SystemConfig).first()
    if not cfg_row:
        raise HTTPException(status_code=500, detail="SystemConfig not seeded")

    config = {
        "ss_rate": cfg_row.ss_rate,
        "medicare_rate": cfg_row.medicare_rate,
        "ss_wage_base": cfg_row.ss_wage_base,
        "futa_rate": cfg_row.futa_rate,
        "futa_wage_base": cfg_row.futa_wage_base,
        "fixed_cost_factor": cfg_row.fixed_cost_factor,
        "loss_fund_factor": cfg_row.loss_fund_factor,
        "pte_weight": cfg_row.pte_weight,
        "wc_policy_adjustment": cfg_row.wc_policy_adjustment,
        "independent_bureau_states": cfg_row.independent_bureau_states or "",
    }

    pay_periods_map = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}

    wc_line_dicts = [l.model_dump() for l in body.wc_lines]
    suta_line_dicts = [l.model_dump() for l in body.suta_lines]

    proposed_mod = 0.0 if body.wc_carve_out else body.proposed_mod
    wc_result = calculate_wc(wc_line_dicts, proposed_mod, config, db=db)

    fica_result = calculate_fica(wc_line_dicts, config)

    futa_result = calculate_futa(wc_line_dicts, body.futa_turnover_rate, config)

    suta_result = calculate_suta(suta_line_dicts)

    total_gws = sum(l.get("annual_gw", 0.0) for l in wc_line_dicts)
    total_wses = futa_result["total_wses"]

    admin_result = calculate_admin(
        total_gws=total_gws,
        total_wses=total_wses,
        method=body.admin_method,
        rate=body.admin_rate,
        pay_frequency=body.payroll_frequency,
        wc_policy_adj=body.wc_policy_adj,
        pay_periods_map=pay_periods_map,
    )

    pay_periods_per_year = pay_periods_map.get(body.payroll_frequency, 26)
    tlm_rate = cfg_row.tlm_rate or 0.0
    wire_ach_rate = cfg_row.wire_ach_rate or 0.0

    commission_result = calculate_commission(
        admin_margin=admin_result["total_admin_fee"],
        wc_billed=wc_result["total_billing"],
        broker_admin_pct=body.external_commission_pct,
        broker_comp_pct=body.broker_wc_commission_pct,
        pool_pct=cfg_row.admin_commission_pool_pct,
        upfront_no_broker=cfg_row.consultant_commission_upfront,
        ongoing_no_broker=cfg_row.consultant_commission_ongoing,
        min_ongoing=cfg_row.consultant_min_ongoing_pct,
    )

    ancillary_full = {
        "implementation_fee": body.implementation_fee,
        "epli_rate": body.epli_rate,
        "tlm_rate": tlm_rate,
        "wire_ach_rate": wire_ach_rate,
        "pay_periods_per_year": pay_periods_per_year,
        "broker_wc_commission_pct": body.broker_wc_commission_pct,
        "external_commission_pct": body.external_commission_pct,
        "consultant_commission_upfront": cfg_row.consultant_commission_upfront,
        "consultant_commission_ongoing": cfg_row.consultant_commission_ongoing,
    }

    proposal_data = build_proposal(wc_result, admin_result, futa_result)
    analysis_data = build_analysis(
        wc_result=wc_result,
        fica_result=fica_result,
        futa_result=futa_result,
        suta_result=suta_result,
        admin_result=admin_result,
        commission_result=commission_result,
        ancillary=ancillary_full,
    )

    return {**proposal_data, **analysis_data, "suta_lines": suta_result["lines"]}

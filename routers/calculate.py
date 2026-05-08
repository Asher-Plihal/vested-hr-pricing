import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import SystemConfig
from schemas import CalculateRequest

from calc.wse import calculate_wses
from calc.workers_comp import calculate_wc
from calc.fica import calculate_fica
from calc.futa import calculate_futa
from calc.suta import calculate_suta
from calc.admin_fee import calculate_admin
from calc.commission import calculate_commission
from calc.summary import calculate_summary

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
    }

    try:
        pay_periods_map = json.loads(cfg_row.pay_periods_json)
    except (json.JSONDecodeError, TypeError):
        pay_periods_map = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}

    wc_line_dicts = [l.model_dump() for l in body.wc_lines]
    suta_line_dicts = [l.model_dump() for l in body.suta_lines]

    proposed_mod = body.proposed_mod
    wc_result = calculate_wc(wc_line_dicts, proposed_mod, config)

    fica_result = calculate_fica(wc_line_dicts, config)

    futa_result = calculate_futa(wc_line_dicts, body.w2s_generated, config)

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

    implementation_fee = body.implementation_fee
    epli_fee = body.epli_fee
    tlm_fee = body.tlm_fee
    wire_ach_fee = body.wire_ach_fee
    total_ancillary = implementation_fee + epli_fee + tlm_fee + wire_ach_fee
    total_with_ancillary = admin_result["total_admin_fee"] + total_ancillary

    commission_result = calculate_commission(
        total_admin_fee=admin_result["total_admin_fee"],
        total_with_ancillary=total_with_ancillary,
        internal_pct=body.internal_commission_pct,
        external_pct=body.external_commission_pct,
    )

    ancillary_full = {
        "implementation_fee": implementation_fee,
        "epli_fee": epli_fee,
        "tlm_fee": tlm_fee,
        "wire_ach_fee": wire_ach_fee,
        "broker_wc_commission_pct": body.broker_wc_commission_pct,
        "external_commission_pct": body.external_commission_pct,
    }

    summary = calculate_summary(
        wc_result=wc_result,
        fica_result=fica_result,
        futa_result=futa_result,
        suta_result=suta_result,
        admin_result=admin_result,
        commission_result=commission_result,
        ancillary=ancillary_full,
    )

    return summary

"""
Analysis & Summary tab — rolls up all calc results into the Deal Summary structure.
  taxes_overview: SUTA billing/cost/profit, FICA total, FUTA total.
  other_items:    TLM, EPLI, wire/ACH fee, implementation fee, total ancillary, total P&L.
  commissions:    consultant upfront/ongoing, broker WC and admin splits, admin net after
                  commissions, cash flow after commissions, 50% loss fund cash flow.
ancillary input: {implementation_fee, epli_rate, tlm_rate, wire_ach_rate,
                  pay_periods_per_year, broker_wc_commission_pct, external_commission_pct}
"""

def build_analysis(
    wc_result: dict,
    fica_result: dict,
    futa_result: dict,
    suta_result: dict,
    admin_result: dict,
    commission_result: dict,
    ancillary: dict,
) -> dict:
    pf = ancillary.get("pay_periods_per_year", 26)
    total_wses = futa_result.get("total_wses", 0.0)

    tlm_fee = ancillary.get("tlm_rate", 0.0) * total_wses * 12
    epli_fee = ancillary.get("epli_rate", 0.0) * total_wses * pf
    wire_ach_fee = ancillary.get("wire_ach_rate", 0.0) * pf
    implementation_fee = ancillary.get("implementation_fee", 0.0)
    total_other = tlm_fee + epli_fee + wire_ach_fee + implementation_fee

    wc_profit = wc_result.get("total_margin", 0.0)
    suta_profit = suta_result.get("total_profit", 0.0)
    admin_fee = admin_result.get("total_admin_fee", 0.0)
    total_comm = commission_result.get("total_commission", 0.0)
    total_comm_rate = total_comm / admin_fee if admin_fee > 0 else 0.0
    internal_comm = commission_result.get("internal_comm", 0.0)
    external_comm = commission_result.get("external_comm", 0.0)
    admin_after_comm = commission_result.get("admin_after_comm", 0.0)
    admin_net_ongoing = commission_result.get("admin_net_ongoing", 0.0)

    broker_wc_pct = ancillary.get("broker_wc_commission_pct", 0.0)
    broker_wc_commission = commission_result.get("broker_comp", 0.0)
    wc_profit_after_broker = wc_profit - broker_wc_commission
    broker_admin_pct = ancillary.get("external_commission_pct", 0.0)

    consultant_upfront_amt  = commission_result.get("consultant_upfront", 0.0)
    consultant_ongoing_amt  = commission_result.get("consultant_ongoing", 0.0)
    consultant_upfront_rate = commission_result.get("consultant_upfront_rate", 0.0)
    consultant_ongoing_rate = commission_result.get("consultant_ongoing_rate", 0.0)
    broker_admin_amt        = commission_result.get("broker_admin", 0.0)

    total_profit_loss = wc_profit_after_broker + suta_profit + admin_after_comm + total_other

    # Year 1 subtracts upfront on top of ongoing; ongoing only subtracts recurring commissions
    admin_net_year1 = admin_after_comm

    # Cash flow approx: subtract 50% loss fund from ongoing net
    cashflow_50pct_loss_fund = admin_after_comm - (wc_result.get("total_loss_fund", 0.0) * 0.5)

    cash_flow_after_comm = admin_fee + wc_profit + suta_profit + total_other - total_comm

    return {
        "taxes_overview": {
            "suta_billed": suta_result.get("total_bill", 0.0),
            "suta_cost": suta_result.get("total_cost", 0.0),
            "suta_profit_loss": suta_profit,
            "fica_total": fica_result.get("total_fica", 0.0),
            "futa_total": futa_result.get("futa_dollars", 0.0),
        },
        "other_items": {
            "tlm": tlm_fee,
            "epli": epli_fee,
            "wire_ach_fee": wire_ach_fee,
            "implementation_fee": implementation_fee,
            "total_ancillary": total_other,
            "total_profit_loss": total_profit_loss,
        },
        "commissions": {
            "consultant_upfront": consultant_upfront_amt,
            "consultant_upfront_rate": consultant_upfront_rate,
            "consultant_ongoing": consultant_ongoing_amt,
            "consultant_ongoing_rate": consultant_ongoing_rate,
            "broker_wc_commission": broker_wc_commission,
            "broker_wc_pct": broker_wc_pct,
            "broker_admin_amt": broker_admin_amt,
            "broker_admin_pct": broker_admin_pct,
            "admin_net_ongoing": admin_net_ongoing,
            "admin_net_year1": admin_net_year1,
            "cashflow_50pct_loss_fund": cashflow_50pct_loss_fund,
            "cash_flow_after_comm": cash_flow_after_comm,
            "internal_comm": internal_comm,
            "external_comm": external_comm,
            "total_comm": total_comm,
            "total_comm_rate": total_comm_rate,
        },
    }

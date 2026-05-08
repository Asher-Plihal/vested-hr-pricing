def calculate_summary(
    wc_result: dict,
    fica_result: dict,
    futa_result: dict,
    suta_result: dict,
    admin_result: dict,
    commission_result: dict,
    ancillary: dict,
) -> dict:
    """
    Rolls up all calc module outputs into the Deal Summary structure
    from pricing_tool_outline.md.
    ancillary: {implementation_fee, epli_fee, tlm_fee, wire_ach_fee}
    """
    total_gws = sum(
        line.get("annual_gw", 0.0) for line in wc_result.get("lines", [])
    )
    total_wses = futa_result.get("total_wses", 0.0)
    avg_wage = total_gws / total_wses if total_wses > 0 else 0.0

    tlm_fee = ancillary.get("tlm_fee", 0.0)
    epli_fee = ancillary.get("epli_fee", 0.0)
    wire_ach_fee = ancillary.get("wire_ach_fee", 0.0)
    implementation_fee = ancillary.get("implementation_fee", 0.0)

    total_other = tlm_fee + epli_fee + wire_ach_fee + implementation_fee

    wc_profit = wc_result.get("total_margin", 0.0)
    suta_profit = suta_result.get("total_profit", 0.0)
    admin_fee = admin_result.get("total_admin_fee", 0.0)
    total_comm = commission_result.get("total_comm", 0.0)
    internal_comm = commission_result.get("internal_comm", 0.0)
    external_comm = commission_result.get("external_comm", 0.0)
    admin_after_comm = commission_result.get("admin_after_comm", 0.0)

    total_profit_loss = wc_profit + suta_profit + admin_after_comm + total_other

    # Year 1 differs from ongoing by removing implementation fee from recurring calculation
    admin_net_year1 = admin_after_comm - implementation_fee

    # Cash flow approx: subtract 50% loss fund from ongoing net
    cashflow_50pct_loss_fund = admin_after_comm - (wc_result.get("total_loss_fund", 0.0) * 0.5)

    return {
        "admin_overview": {
            "total_wses": total_wses,
            "total_gws": total_gws,
            "avg_wage": avg_wage,
            "admin_margin": admin_fee,
        },
        "wc_overview": {
            "wc_billed": wc_result.get("total_billing", 0.0),
            "wc_fixed_cost": wc_result.get("total_fixed_cost", 0.0),
            "wc_loss_fund": wc_result.get("total_loss_fund", 0.0),
            "total_wc_cost": wc_result.get("total_cost", 0.0),
            "wc_profit_loss": wc_profit,
        },
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
            "total_profit_loss": total_profit_loss,
        },
        "commissions": {
            "consultant_upfront": admin_fee * 0.25,
            "consultant_ongoing": admin_fee * 0.20,
            "broker_wc_pct": ancillary.get("broker_wc_commission_pct", 0.0),
            "broker_admin_pct": ancillary.get("external_commission_pct", 0.0),
            "admin_net_ongoing": admin_after_comm,
            "admin_net_year1": admin_net_year1,
            "cashflow_50pct_loss_fund": cashflow_50pct_loss_fund,
            "internal_comm": internal_comm,
            "external_comm": external_comm,
            "total_comm": total_comm,
        },
    }

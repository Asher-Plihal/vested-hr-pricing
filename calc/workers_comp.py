def calculate_wc(lines: list[dict], proposed_mod: float, config: dict) -> dict:
    """
    lines: [{state, wc_code, annual_gw, ftes, ptes, current_client_rate, manual_rate}]
    proposed_mod == 0 means full carve-out; all billing zeros out.
    manual_rate is passed directly — WC Rates table lookup not yet implemented.
    """
    fixed_cost_factor = config["fixed_cost_factor"]
    loss_fund_factor = config["loss_fund_factor"]
    pte_weight = config.get("pte_weight", 0.75)

    result_lines = []
    total_billing = 0.0
    total_cost = 0.0
    total_margin = 0.0
    total_current_billing = 0.0
    total_current_margin = 0.0
    total_followup_margin = 0.0
    total_followup_billing = 0.0

    for line in lines:
        gw = line.get("annual_gw", 0.0)
        ftes = line.get("ftes", 0.0)
        ptes = line.get("ptes", 0.0)
        manual_rate = line.get("manual_rate", 0.0)
        current_client_rate = line.get("current_client_rate", 0.0)

        wses = ftes + pte_weight * ptes

        if proposed_mod == 0:
            billing = 0.0
            cost = 0.0
            margin = 0.0
        else:
            billing = (manual_rate * proposed_mod) * gw / 100
            cost = billing * (fixed_cost_factor + loss_fund_factor)
            margin = billing - cost

        current_eff_rate = current_client_rate * proposed_mod if proposed_mod != 0 else 0.0
        current_billing = gw * current_eff_rate / 100
        current_cost = billing  # same cost structure applied to current billing
        current_margin = current_billing - current_cost
        followup_margin = current_margin - margin
        followup_billing = current_billing - billing

        result_lines.append({
            "state": line.get("state"),
            "wc_code": line.get("wc_code"),
            "wses": wses,
            "annual_gw": gw,
            "manual_rate": manual_rate,
            "billing": billing,
            "cost": cost,
            "margin": margin,
            "current_eff_rate": current_eff_rate,
            "current_billing": current_billing,
            "current_cost": current_cost,
            "current_margin": current_margin,
            "followup_margin": followup_margin,
            "followup_billing": followup_billing,
        })

        total_billing += billing
        total_cost += cost
        total_margin += margin
        total_current_billing += current_billing
        total_current_margin += current_margin
        total_followup_margin += followup_margin
        total_followup_billing += followup_billing

    return {
        "lines": result_lines,
        "total_billing": total_billing,
        "total_cost": total_cost,
        "total_margin": total_margin,
        "total_fixed_cost": total_billing * fixed_cost_factor,
        "total_loss_fund": total_billing * loss_fund_factor,
        "total_current_billing": total_current_billing,
        "total_current_margin": total_current_margin,
        "total_followup_margin": total_followup_margin,
        "total_followup_billing": total_followup_billing,
    }

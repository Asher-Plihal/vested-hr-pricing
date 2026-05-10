"""
Taxes tab — three tax passthroughs bundled together:
  FICA:  Social Security (per-WSE wage-base cap) + Medicare, no VHR margin.
  FUTA:  Approach B only — WSEs × $7K wage base × 0.6% × turnover rate.
         turnover_rate is a decimal; can exceed 1.0 when W-2s outnumber avg headcount.
  SUTA:  Per-state billing/cost/profit using VHR rates from the suta_rates table.
         ~22 states are client-reporting (PT) and excluded from VHR billing math.
"""

# ── FICA

def calculate_fica(lines: list[dict], config: dict) -> dict:
    """
    lines: [{annual_gw, ftes, ptes}]
    SS cap applied per-line using WSE count as a proxy (approximation — see pricing_math.md notes).
    Pure passthrough: no VHR margin.
    """
    ss_rate = config["ss_rate"]
    medicare_rate = config["medicare_rate"]
    ss_wage_base = config["ss_wage_base"]
    pte_weight = config.get("pte_weight", 0.75)

    total_ss = 0.0
    total_medicare = 0.0

    for line in lines:
        gw = line.get("annual_gw", 0.0)
        ftes = line.get("ftes", 0.0)
        ptes = line.get("ptes", 0.0)
        wses = ftes + pte_weight * ptes

        taxable_ss_wages = min(gw, wses * ss_wage_base)
        total_ss += taxable_ss_wages * ss_rate
        total_medicare += gw * medicare_rate

    total_fica = total_ss + total_medicare

    return {
        "ss_dollars": total_ss,
        "medicare_dollars": total_medicare,
        "total_fica": total_fica,
    }


# ── FUTA

def calculate_futa(lines: list[dict], turnover_rate: float, config: dict) -> dict:
    futa_rate = config["futa_rate"]
    futa_wage_base = config["futa_wage_base"]
    pte_weight = config.get("pte_weight", 0.75)

    total_wses = sum(
        line.get("ftes", 0.0) + pte_weight * line.get("ptes", 0.0)
        for line in lines
    )

    futa_dollars = total_wses * futa_wage_base * futa_rate * turnover_rate

    return {
        "futa_dollars": futa_dollars,
        "turnover_pct": turnover_rate,
        "total_wses": total_wses,
    }


# ── SUTA

def calculate_suta(suta_lines: list[dict]) -> dict:
    """
    suta_lines: [{state, gws, total_wses, billing_rate, cost_rate, threshold,
                  turnover_pct, current_client_rate}]
    """
    result_lines = []
    total_bill = 0.0
    total_cost = 0.0
    total_profit = 0.0
    total_savings = 0.0

    for line in suta_lines:
        gws = line.get("gws", 0.0)
        total_wses = line.get("total_wses", 0.0)
        billing_rate = line.get("billing_rate", 0.0)
        cost_rate = line.get("cost_rate", 0.0)
        threshold = line.get("threshold", 0.0)
        turnover_pct = line.get("turnover_pct", 0.10)
        current_client_rate = line.get("current_client_rate", 0.0)

        wses_with_turnover = total_wses * (1 + turnover_pct)
        taxable_gws = min(gws, threshold * wses_with_turnover)
        suta_bill = billing_rate * taxable_gws
        suta_cost = cost_rate * taxable_gws
        suta_profit = suta_bill - suta_cost
        prior_cost = current_client_rate * taxable_gws
        client_savings = prior_cost - suta_bill

        result_lines.append({
            "state": line.get("state"),
            "taxable_gws": taxable_gws,
            "suta_bill": suta_bill,
            "suta_cost": suta_cost,
            "suta_profit": suta_profit,
            "prior_cost": prior_cost,
            "client_savings": client_savings,
        })

        total_bill += suta_bill
        total_cost += suta_cost
        total_profit += suta_profit
        total_savings += client_savings

    return {
        "lines": result_lines,
        "total_bill": total_bill,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_savings": total_savings,
    }

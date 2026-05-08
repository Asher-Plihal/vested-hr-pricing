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

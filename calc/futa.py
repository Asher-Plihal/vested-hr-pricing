def calculate_futa(lines: list[dict], turnover_rate: float, config: dict) -> dict:
    """
    Approach B only (per pricing_math.md — see notes on Approach A vs B tradeoffs).
    Pure passthrough: no VHR margin.
    turnover_rate is a decimal (e.g. 1.51 = 151% — W-2s can exceed headcount).
    """
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

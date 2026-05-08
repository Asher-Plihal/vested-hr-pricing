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

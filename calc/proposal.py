"""
Proposal tab — rolls up WC and admin results into the two summary dicts consumed by
renderProposal (per-line billing view) and renderBillingAnalysis (current vs. VHR
savings comparison) in client.html.
  admin_overview: total_wses, total_gws, avg_wage, admin_margin
  wc_overview:    wc_billed, wc_fixed_cost, wc_loss_fund, total_wc_cost, wc_profit_loss
"""

def build_proposal(wc_result: dict, admin_result: dict, futa_result: dict) -> dict:
    total_gws = sum(line.get("annual_gw", 0.0) for line in wc_result.get("lines", []))
    total_wses = futa_result.get("total_wses", 0.0)
    avg_wage = total_gws / total_wses if total_wses > 0 else 0.0

    return {
        "admin_overview": {
            "total_wses": total_wses,
            "total_gws": total_gws,
            "avg_wage": avg_wage,
            "admin_margin": admin_result.get("total_admin_fee", 0.0),
        },
        "wc_overview": {
            "wc_billed": wc_result.get("total_billing", 0.0),
            "wc_fixed_cost": wc_result.get("total_fixed_cost", 0.0),
            "wc_loss_fund": wc_result.get("total_loss_fund", 0.0),
            "total_wc_cost": wc_result.get("total_cost", 0.0),
            "wc_profit_loss": wc_result.get("total_margin", 0.0),
        },
    }

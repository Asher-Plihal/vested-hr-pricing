"""
Admin tab — calculates the admin fee using one of three methods:
  1 (% of GWs):   rate × total gross wages, with optional wc_policy_adj added to the rate.
  2 (per-check):  rate × WSEs × pay periods per year.
  3 (PEPM):       rate × WSEs × 12.
Returns total_admin_fee plus per-check and per-WSE-per-month equivalents for all methods.
"""

def calculate_admin(
    total_gws: float,
    total_wses: float,
    method: int,
    rate: float,
    pay_frequency: str,
    wc_policy_adj: float = 0.0,
    pay_periods_map: dict = None,
) -> dict:
    if pay_periods_map is None:
        pay_periods_map = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12}

    pay_periods = pay_periods_map.get(pay_frequency, 26)

    if method == 1:
        total_admin_pct = wc_policy_adj + rate
        total_admin = total_admin_pct * total_gws
        per_check = total_admin / total_wses / pay_periods if total_wses > 0 else 0.0
        per_wse_mo = total_admin / total_wses / 12 if total_wses > 0 else 0.0

    elif method == 2:
        total_admin = rate * total_wses * pay_periods
        total_admin_pct = total_admin / total_gws if total_gws > 0 else 0.0
        per_check = rate
        per_wse_mo = total_admin / total_wses / 12 if total_wses > 0 else 0.0

    elif method == 3:
        total_admin = rate * total_wses * 12
        total_admin_pct = total_admin / total_gws if total_gws > 0 else 0.0
        per_check = total_admin / total_wses / pay_periods if total_wses > 0 else 0.0
        per_wse_mo = rate

    else:
        raise ValueError(f"Unknown admin method: {method}")

    return {
        "total_admin_fee": total_admin,
        "admin_pct": total_admin_pct,
        "per_check_equiv": per_check,
        "per_wse_mo_equiv": per_wse_mo,
    }

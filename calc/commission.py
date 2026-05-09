def calculate_commission(
    admin_margin: float,
    wc_billed: float,
    broker_admin_pct: float,
    broker_comp_pct: float,
    pool_pct: float = 0.40,
    upfront_no_broker: float = 0.25,
    ongoing_no_broker: float = 0.20,
    min_ongoing: float = 0.10,
) -> dict:
    broker_admin = broker_admin_pct * admin_margin
    broker_comp  = broker_comp_pct  * wc_billed

    consultant_base = admin_margin - broker_admin

    has_broker = broker_admin_pct > 0 or broker_comp_pct > 0

    if not has_broker:
        upfront_rate = upfront_no_broker
        ongoing_rate = ongoing_no_broker
    elif broker_admin_pct > 0:
        upfront_rate = 0.0
        ongoing_rate = max(min_ongoing, pool_pct - broker_admin_pct)
    else:
        # broker on comp only, no admin — consultant keeps full admin pool but capped at minimum
        upfront_rate = 0.0
        ongoing_rate = min_ongoing

    consultant_upfront = upfront_rate * consultant_base
    consultant_ongoing = ongoing_rate * consultant_base

    total_commission = consultant_upfront + consultant_ongoing + broker_admin + broker_comp
    admin_net_ongoing = admin_margin - consultant_ongoing - broker_admin
    admin_net_all     = admin_net_ongoing - consultant_upfront

    return {
        "consultant_upfront_rate": upfront_rate,
        "consultant_ongoing_rate": ongoing_rate,
        "consultant_upfront": consultant_upfront,
        "consultant_ongoing": consultant_ongoing,
        "broker_admin": broker_admin,
        "broker_comp": broker_comp,
        "total_commission": total_commission,
        "admin_net_ongoing": admin_net_ongoing,
        "admin_net_all": admin_net_all,
        # legacy keys kept for summary.py compatibility
        "internal_comm": consultant_upfront + consultant_ongoing,
        "external_comm": broker_admin + broker_comp,
        "admin_after_comm": admin_net_all,
    }

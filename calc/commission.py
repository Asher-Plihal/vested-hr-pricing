def calculate_commission(
    total_admin_fee: float,
    total_with_ancillary: float,
    internal_pct: float,
    external_pct: float,
) -> dict:
    """
    Internal commission base is admin fee only (before ancillary).
    External commission base is total with ancillary — external brokers earn on ancillary, internal staff don't.
    """
    if external_pct > 0:
        internal_comm = total_admin_fee * (1 - external_pct) * internal_pct
    else:
        internal_comm = total_admin_fee * internal_pct

    external_comm = total_with_ancillary * external_pct
    total_comm = internal_comm + external_comm
    admin_after_comm = total_with_ancillary - total_comm

    return {
        "internal_comm": internal_comm,
        "external_comm": external_comm,
        "total_comm": total_comm,
        "admin_after_comm": admin_after_comm,
    }

from pydantic import BaseModel
from schemas.workers_comp import WCLineIn
from schemas.taxes import SutaLineIn


class CalculateRequest(BaseModel):
    # Flat fields (used by smoke test and client page)
    ftes: float = 0.0
    ptes: float = 0.0
    futa_turnover_rate: float = 1.0
    wc_lines: list[WCLineIn] = []
    suta_lines: list[SutaLineIn] = []
    proposed_mod: float = 1.0
    wc_carve_out: bool = False
    admin_method: int = 1
    admin_rate: float = 0.0
    payroll_frequency: str = "biweekly"
    wc_policy_adj: float = 0.0
    internal_commission_pct: float = 0.0
    external_commission_pct: float = 0.0
    broker_wc_commission_pct: float = 0.0
    implementation_fee: float = 0.0
    epli_rate: float = 0.0

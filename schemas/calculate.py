"""
Defines the shape of the data sent to the pricing engine. CalculateRequest is a flat
snapshot of everything the calculator needs to produce a deal summary — headcount,
payroll, WC lines, SUTA lines, admin fee method, commission percentages, and any
additional fees. This is assembled by the client form on every field change and sent
to POST /calculate. Nothing is saved to the database; it is purely for live calculation.
"""
from pydantic import BaseModel
from schemas.workers_comp import WCLineIn
from schemas.taxes import SutaLineIn


class CalculateRequest(BaseModel):
    # Flat fields (used by smoke test and client page)
    ftes: float = 0.0
    ptes: float = 0.0
    futa_turnover_rate: float = 0.1
    wc_lines: list[WCLineIn] = []
    suta_lines: list[SutaLineIn] = []
    proposed_mod: float = 1.0
    admin_method: int = 1
    admin_rate: float = 0.0
    admin_rate_2: float = 0.0
    admin_rate_3: float = 0.0
    payroll_frequency: str = "biweekly"
    wc_policy_adj: float = 0.0
    internal_commission_pct: float = 0.0
    external_commission_pct: float = 0.0
    broker_wc_commission_pct: float = 0.0
    implementation_fee: float = 0.0
    epli_rate: float = 0.0
    method_of_payment: str = ""
    use_tlm: bool = True

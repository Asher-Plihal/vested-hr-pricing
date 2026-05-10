"""
Defines the shape of workers comp sub-line data. WCLineIn is one class code row as it
comes in from the form — state, code, payroll, headcount, and rates. WCLineOut adds the
database id fields for responses. WCLossIn and WCLossOut do the same for loss history
rows — coverage period, total losses, claim count, and open claims.
"""
from typing import Optional
from pydantic import BaseModel


class WCLineIn(BaseModel):
    state: Optional[str] = None
    wc_code: Optional[str] = None
    wc_description: Optional[str] = None
    hazard_group: Optional[str] = None
    flag_100k: Optional[str] = None
    annual_gw: float = 0.0
    ftes: float = 0.0
    ptes: float = 0.0
    current_client_rate: float = 0.0
    manual_rate: float = 0.0


class WCLineOut(WCLineIn):
    id: int
    contact_id: int
    model_config = {"from_attributes": True}


class WCLossIn(BaseModel):
    coverage_period_start: Optional[str] = None
    coverage_period_end: Optional[str] = None
    total_losses_incurred: float = 0.0
    num_claims: int = 0
    months_in_policy: int = 0
    open_claims: int = 0


class WCLossOut(WCLossIn):
    id: int
    contact_id: int
    model_config = {"from_attributes": True}

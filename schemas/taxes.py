from typing import Optional
from pydantic import BaseModel


class SutaLineIn(BaseModel):
    state: Optional[str] = None
    gws: float = 0.0
    total_wses: float = 0.0
    current_client_rate: float = 0.0
    billing_rate: float = 0.0
    cost_rate: float = 0.0
    threshold: float = 0.0
    turnover_pct: float = 0.10


class SutaLineOut(SutaLineIn):
    id: int
    client_id: int
    model_config = {"from_attributes": True}


class SutaRateOut(BaseModel):
    id: int
    state: str
    threshold: Optional[float]
    vhr_min_rate: Optional[float]
    client_reporting: bool
    our_cost: Optional[float]
    model_config = {"from_attributes": True}


class SutaRateUpdate(BaseModel):
    state: str
    threshold: Optional[float] = None
    vhr_min_rate: Optional[float] = None
    client_reporting: Optional[bool] = None
    our_cost: Optional[float] = None

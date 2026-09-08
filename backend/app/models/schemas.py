from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ForecastRequest(BaseModel):
    origin: str
    vessel: str
    horizons: List[int] = [7, 14, 30, 60]


class VesselOptimizeRequest(BaseModel):
    origin: str
    destination: str
    cargo: str = "coking_coal"
    cargo_mt: float = 80000
    bunker_price: float = 520.0
    extra_waiting_hrs: float = 0.0


class PortCheckRequest(BaseModel):
    origin: str
    destination: str
    vessel: str
    cargo: str = "coking_coal"


class VoyageCostRequest(BaseModel):
    origin: str
    destination: str
    vessel: str
    cargo_mt: float
    freight_rate: Optional[float] = None
    bunker_price: float = 520.0
    extra_waiting_hrs: float = 0.0


class ContractRequest(BaseModel):
    origin: str
    vessel: str
    cargo_mt: float = 80000
    num_voyages: int = 6
    risk_tolerance: str = "medium"


class IdleRequest(BaseModel):
    vessel: str
    current_port: str


class RiskRequest(BaseModel):
    origin: str
    destination: str
    vessel: str
    cargo_mt: float = 80000


class DecisionRequest(BaseModel):
    origin: str = Field(..., example="Newcastle")
    destination: str = Field(..., example="Paradip")
    cargo: str = Field("coking_coal", example="coking_coal")
    cargo_mt: float = Field(80000, example=80000)
    laycan_start: Optional[str] = Field(None, example="2026-11-01")
    bunker_price: float = 520.0
    extra_waiting_hrs: float = 0.0
    risk_tolerance: str = "medium"
    num_voyages: int = 6


class ScenarioRequest(BaseModel):
    base: DecisionRequest
    freight_pct_change: float = 0.0
    bunker_pct_change: float = 0.0
    extra_waiting_hrs: float = 0.0
    cargo_mt_override: Optional[float] = None
    destination_override: Optional[str] = None

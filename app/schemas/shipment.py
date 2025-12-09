from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ShipmentStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    ARRIVED = "arrived"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"

class ShipmentMode(str, Enum):
    AIR = "air"
    SEA = "sea"
    LAND = "land"
    RAIL = "rail"
    MULTIMODAL = "multimodal"

class ShipmentBase(BaseModel):
    tracking_number: str
    reference_number: Optional[str] = None
    origin: str
    destination: str
    mode: ShipmentMode
    weight: Optional[float] = None
    volume: Optional[float] = None
    value: Optional[float] = None
    estimated_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    shipper: Optional[str] = None
    carrier: Optional[str] = None
    consignee: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentUpdate(BaseModel):
    current_location: Optional[str] = None
    status: Optional[ShipmentStatus] = None
    current_port: Optional[str] = None
    next_port: Optional[str] = None
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class ShipmentInDB(ShipmentBase):
    id: int
    status: ShipmentStatus
    current_location: Optional[str] = None
    current_port: Optional[str] = None
    next_port: Optional[str] = None
    is_at_risk: bool = False
    risk_score: float = 0.0
    last_risk_check: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ShipmentWithRelations(ShipmentInDB):
    risks: List["RiskInDB"] = []
    events: List["ShipmentEventInDB"] = []
    simulations: List["SimulationInDB"] = []
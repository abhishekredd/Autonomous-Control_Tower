from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.schemas.risk import RiskInDB
from app.schemas.simulation import SimulationInDB

# --- ShipmentEvent schemas ---
class ShipmentEventBase(BaseModel):
    event_type: str
    location: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime
    event_metadata: Dict[str, Any] = {}

class ShipmentEventCreate(ShipmentEventBase):
    shipment_id: int

class ShipmentEventInDB(ShipmentEventBase):
    id: int
    shipment_id: int

    class Config:
        from_attributes = True

# --- ShipmentRoute schemas ---
class ShipmentRouteBase(BaseModel):
    route_type: str  # original, alternative, executed
    waypoints: List[Dict[str, Any]]  # list of waypoints with coordinates
    total_distance: Optional[float] = None
    estimated_duration: Optional[float] = None  # hours
    cost_estimate: Optional[float] = None
    risk_score: Optional[float] = None
    is_active: bool = False

class ShipmentRouteCreate(ShipmentRouteBase):
    shipment_id: int

class ShipmentRouteInDB(ShipmentRouteBase):
    id: int
    shipment_id: int

    class Config:
        from_attributes = True

# --- Shipment schemas ---
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
    risks: List[RiskInDB] = []
    events: List[ShipmentEventInDB] = []
    simulations: List[SimulationInDB] = []
    routes: List[ShipmentRouteInDB] = []

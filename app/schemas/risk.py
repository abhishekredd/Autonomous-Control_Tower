from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskStatus(str, Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class RiskType(str, Enum):
    PORT_CONGESTION = "port_congestion"
    CUSTOMS_DELAY = "customs_delay"
    QUALITY_HOLD = "quality_hold"
    WEATHER_IMPACT = "weather_impact"
    EQUIPMENT_FAILURE = "equipment_failure"
    LABOR_STRIKE = "labor_strike"
    SECURITY_ISSUE = "security_issue"
    ROUTE_BLOCKAGE = "route_blockage"
    CAPACITY_SHORTAGE = "capacity_shortage"
    OTHER = "other"

class RiskBase(BaseModel):
    shipment_id: int
    risk_type: RiskType
    severity: RiskSeverity
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    expected_delay_hours: Optional[float] = None
    expected_cost_impact: Optional[float] = None

class RiskCreate(RiskBase):
    pass

class RiskUpdate(BaseModel):
    status: Optional[RiskStatus] = None
    mitigation_actions: Optional[List[Dict[str, Any]]] = None
    selected_mitigation: Optional[Dict[str, Any]] = None
    mitigation_result: Optional[Dict[str, Any]] = None
    resolved_at: Optional[datetime] = None

class RiskInDB(RiskBase):
    id: int
    status: RiskStatus
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    affected_parties: List[str] = Field(default_factory=list)
    mitigation_actions: List[Dict[str, Any]] = Field(default_factory=list)
    selected_mitigation: Optional[Dict[str, Any]] = None
    mitigation_result: Optional[Dict[str, Any]] = None
    source: str = "system"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationType(str, Enum):
    MITIGATION_ANALYSIS = "mitigation_analysis"
    ROUTE_OPTIMIZATION = "route_optimization"
    WHAT_IF_SCENARIO = "what_if_scenario"
    COST_BENEFIT = "cost_benefit"

class SimulationBase(BaseModel):
    shipment_id: int
    simulation_type: SimulationType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    scenario_description: Optional[str] = None

class SimulationCreate(SimulationBase):
    pass

class SimulationUpdate(BaseModel):
    status: Optional[SimulationStatus] = None
    results: Optional[Dict[str, Any]] = None
    best_option: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    execution_time: Optional[float] = None

class SimulationInDB(SimulationBase):
    id: int
    status: SimulationStatus
    results: Optional[Dict[str, Any]] = None
    best_option: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    initiated_by: str = "system"
    execution_time: Optional[float] = None
    simulation_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
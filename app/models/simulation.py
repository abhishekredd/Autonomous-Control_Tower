from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedBase
import enum

class SimulationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SimulationType(str, enum.Enum):
    MITIGATION_ANALYSIS = "mitigation_analysis"
    ROUTE_OPTIMIZATION = "route_optimization"
    WHAT_IF_SCENARIO = "what_if_scenario"
    COST_BENEFIT = "cost_benefit"

class Simulation(TimeStampedBase):
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    simulation_type = Column(Enum(SimulationType))
    status = Column(Enum(SimulationStatus), default=SimulationStatus.PENDING)
    
    # Input parameters
    parameters = Column(JSON, default={})
    scenario_description = Column(Text)
    
    # Results
    results = Column(JSON)  # All simulation results
    best_option = Column(JSON)  # Best option identified
    confidence_score = Column(Float)
    
    # Metadata
    initiated_by = Column(String)  # MCP agent, user, system
    execution_time = Column(Float)  # seconds
    metadata = Column(JSON, default={})
    
    # Relationships
    shipment = relationship("Shipment", back_populates="simulations")
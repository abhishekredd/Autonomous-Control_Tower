from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedBase
import enum

class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    ARRIVED = "arrived"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"

class ShipmentMode(str, enum.Enum):
    AIR = "air"
    SEA = "sea"
    LAND = "land"
    RAIL = "rail"
    MULTIMODAL = "multimodal"

class Shipment(TimeStampedBase):
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True)
    reference_number = Column(String, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    current_location = Column(String)
    current_port = Column(String)
    next_port = Column(String)
    
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    mode = Column(Enum(ShipmentMode), nullable=False)
    
    # Dimensions
    weight = Column(Float)
    volume = Column(Float)
    value = Column(Float)
    
    # Timestamps
    estimated_departure = Column(DateTime)
    estimated_arrival = Column(DateTime)
    actual_departure = Column(DateTime)
    actual_arrival = Column(DateTime)
    
    # Stakeholders
    shipper = Column(String)
    carrier = Column(String)
    consignee = Column(String)
    customs_broker = Column(String)
    
    # Risk flags
    is_at_risk = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    last_risk_check = Column(DateTime)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Relationships
    risks = relationship("Risk", back_populates="shipment", cascade="all, delete-orphan")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="shipment", cascade="all, delete-orphan")

class ShipmentEvent(TimeStampedBase):
    __tablename__ = "shipment_events"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    event_type = Column(String)
    location = Column(String)
    description = Column(String)
    timestamp = Column(DateTime)
    metadata = Column(JSON, default={})
    
    shipment = relationship("Shipment", back_populates="events")

class ShipmentRoute(TimeStampedBase):
    __tablename__ = "shipment_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    route_type = Column(String)  # original, alternative, executed
    waypoints = Column(JSON)  # List of waypoints with coordinates
    total_distance = Column(Float)
    estimated_duration = Column(Float)  # hours
    cost_estimate = Column(Float)
    risk_score = Column(Float)
    is_active = Column(Boolean, default=False)
    
    shipment = relationship("Shipment")
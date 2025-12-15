from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedBase
import enum

class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskStatus(str, enum.Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class RiskType(str, enum.Enum):
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

class Risk(TimeStampedBase):
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    # Store enum-backed fields as plain strings to avoid SQLAlchemy mapping enum
    # member names (which can be uppercase) to Postgres enum labels. The DB
    # still uses user-defined enum types; passing plain lowercase strings that
    # match the enum labels is the most reliable approach across drivers.
    risk_type = Column(String)
    severity = Column(String)
    status = Column(String, default=RiskStatus.DETECTED.value)
    
    description = Column(Text)
    confidence = Column(Float)  # 0.0 to 1.0
    detected_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Impact assessment
    expected_delay_hours = Column(Float)
    expected_cost_impact = Column(Float)
    affected_parties = Column(JSON)  # List of affected stakeholders
    
    # Mitigation
    mitigation_actions = Column(JSON)  # List of proposed actions
    selected_mitigation = Column(JSON)  # Selected action
    mitigation_result = Column(JSON)  # Result of mitigation
    
    # Metadata
    source = Column(String)  # MCP agent, manual, external API
    risk_metadata = Column(JSON, default=dict)
    
    # Relationships
    shipment = relationship("Shipment", back_populates="risks")
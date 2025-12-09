from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.risk import Risk, RiskStatus, RiskSeverity
from app.models.shipment import Shipment
from app.schemas.risk import RiskCreate, RiskUpdate

class RiskService:
    """Service for risk detection and management"""
    
    async def detect_risks(self, shipment_id: int, session: AsyncSession) -> List[Risk]:
        """Detect risks for a shipment"""
        risks = []
        
        # Get shipment data
        shipment = await session.get(Shipment, shipment_id)
        if not shipment:
            return risks
        
        # Check for various risk types
        risks.extend(await self._detect_port_congestion(shipment, session))
        risks.extend(await self._detect_customs_delays(shipment, session))
        risks.extend(await self._detect_quality_holds(shipment, session))
        risks.extend(await self._detect_delays(shipment, session))
        
        return risks
    
    async def _detect_port_congestion(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect port congestion risks"""
        risks = []
        
        if shipment.next_port:
            # Check congestion at next port
            congestion_level = await self._get_congestion_level(shipment.next_port)
            
            if congestion_level > 0.7:
                risk = Risk(
                    shipment_id=shipment.id,
                    risk_type="port_congestion",
                    severity=RiskSeverity.HIGH if congestion_level > 0.8 else RiskSeverity.MEDIUM,
                    description=f"Port congestion detected at {shipment.next_port}",
                    confidence=congestion_level,
                    detected_at=datetime.utcnow(),
                    status=RiskStatus.DETECTED,
                    expected_delay_hours=congestion_level * 48,
                    metadata={"port": shipment.next_port, "congestion_level": congestion_level}
                )
                risks.append(risk)
        
        return risks
    
    async def _detect_customs_delays(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect customs delay risks"""
        risks = []
        
        customs_status = shipment.metadata.get("customs_status")
        if customs_status in ["delayed", "held", "under_review"]:
            risk = Risk(
                shipment_id=shipment.id,
                risk_type="customs_delay",
                severity=RiskSeverity.HIGH,
                description=f"Customs clearance {customs_status}",
                confidence=0.85,
                detected_at=datetime.utcnow(),
                status=RiskStatus.DETECTED,
                expected_delay_hours=24,
                metadata={"customs_status": customs_status}
            )
            risks.append(risk)
        
        return risks
    
    async def _detect_quality_holds(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect quality hold risks"""
        risks = []
        
        quality_status = shipment.metadata.get("quality_status")
        if quality_status in ["hold", "inspection"]:
            risk = Risk(
                shipment_id=shipment.id,
                risk_type="quality_hold",
                severity=RiskSeverity.MEDIUM,
                description=f"Quality inspection {quality_status}",
                confidence=0.9,
                detected_at=datetime.utcnow(),
                status=RiskStatus.DETECTED,
                expected_delay_hours=12,
                metadata={"quality_status": quality_status}
            )
            risks.append(risk)
        
        return risks
    
    async def _detect_delays(self, shipment: Shipment, session: AsyncSession) -> List[Risk]:
        """Detect delay risks"""
        risks = []
        
        if shipment.estimated_arrival and datetime.utcnow() > shipment.estimated_arrival:
            delay_hours = (datetime.utcnow() - shipment.estimated_arrival).total_seconds() / 3600
            
            if delay_hours > 4:
                risk = Risk(
                    shipment_id=shipment.id,
                    risk_type="other",
                    severity=RiskSeverity.HIGH if delay_hours > 24 else RiskSeverity.MEDIUM,
                    description=f"Shipment delayed by {delay_hours:.1f} hours",
                    confidence=min(0.9, delay_hours / 48),
                    detected_at=datetime.utcnow(),
                    status=RiskStatus.DETECTED,
                    expected_delay_hours=delay_hours,
                    metadata={"delay_hours": delay_hours}
                )
                risks.append(risk)
        
        return risks
    
    async def _get_congestion_level(self, port_code: str) -> float:
        """Get congestion level for a port"""
        # Simplified - in production, this would call an external API
        congestion_data = {
            "CNSHA": 0.8,
            "USLAX": 0.7,
            "SGSIN": 0.4,
            "NLRTM": 0.6
        }
        return congestion_data.get(port_code, 0.3)
    
    async def get_shipment_risks(self, shipment_id: int, session: AsyncSession) -> List[Risk]:
        """Get all risks for a shipment"""
        result = await session.execute(
            select(Risk).where(Risk.shipment_id == shipment_id)
        )
        return result.scalars().all()
    
    async def update_risk_status(self, risk_id: int, status: RiskStatus,
                               session: AsyncSession) -> Optional[Risk]:
        """Update risk status"""
        risk = await session.get(Risk, risk_id)
        if risk:
            risk.status = status
            if status == RiskStatus.RESOLVED:
                risk.resolved_at = datetime.utcnow()
            await session.commit()
            await session.refresh(risk)
        return risk
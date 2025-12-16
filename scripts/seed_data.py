import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.shipment import Shipment, ShipmentStatus, ShipmentMode
from app.models.risk import Risk, RiskType, RiskSeverity, RiskStatus

async def create_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")

async def seed_shipments():
    """Seed sample shipments"""
    async with AsyncSessionLocal() as session:
        # Sample shipments
        shipments = [
            Shipment(
                tracking_number="TRK789012",
                reference_number="SH-001",
                origin="Shanghai, China",
                destination="Rotterdam, Netherlands",
                current_location="Pacific Ocean",
                current_port=None,
                next_port="NLRTM",
                status=ShipmentStatus.IN_TRANSIT,
                mode=ShipmentMode.SEA,
                weight=25000,
                volume=68,
                value=500000,
                estimated_departure=datetime.utcnow() - timedelta(days=12),
                estimated_arrival=datetime.utcnow() + timedelta(days=3),
                shipper="Acme Corporation",
                carrier="Maersk Line",
                consignee="Global Imports BV",
                customs_broker="Quick Clear Customs",
                is_at_risk=True,
                risk_score=0.82,
                last_risk_check=datetime.utcnow(),
                metadata={
                    "container_number": "MSKU1234567",
                    "vessel": "MSC Diana",
                    "customs_status": "pre_cleared",
                    "quality_status": "clear",
                    "insurance_value": 550000
                }
            ),
            Shipment(
                tracking_number="TRK789013",
                reference_number="SH-002",
                origin="Los Angeles, USA",
                destination="Tokyo, Japan",
                current_location="Los Angeles Port",
                current_port="USLAX",
                next_port="JPTYO",
                status=ShipmentStatus.DELAYED,
                mode=ShipmentMode.SEA,
                weight=18000,
                volume=45,
                value=320000,
                estimated_departure=datetime.utcnow() - timedelta(days=2),
                estimated_arrival=datetime.utcnow() + timedelta(days=14),
                shipper="Tech Supplies Inc",
                carrier="COSCO Shipping",
                consignee="Japan Electronics Corp",
                customs_broker="Nippon Customs",
                is_at_risk=True,
                risk_score=0.91,
                last_risk_check=datetime.utcnow(),
                metadata={
                    "container_number": "COSCO987654",
                    "vessel": "COSCO Harmony",
                    "customs_status": "held",
                    "quality_status": "inspection",
                    "delay_reason": "port_congestion"
                }
            ),
            Shipment(
                tracking_number="TRK789014",
                reference_number="SH-003",
                origin="Singapore",
                destination="Dubai, UAE",
                current_location="Singapore Port",
                current_port="SGSIN",
                next_port="AEDXB",
                status=ShipmentStatus.IN_TRANSIT,
                mode=ShipmentMode.AIR,
                weight=5000,
                volume=12,
                value=150000,
                estimated_departure=datetime.utcnow() - timedelta(hours=6),
                estimated_arrival=datetime.utcnow() + timedelta(hours=10),
                shipper="Singapore Exports",
                carrier="Emirates SkyCargo",
                consignee="Dubai Trading Co",
                customs_broker="Gulf Customs",
                is_at_risk=False,
                risk_score=0.15,
                last_risk_check=datetime.utcnow() - timedelta(hours=2),
                metadata={
                    "flight_number": "EK405",
                    "airway_bill": "157-12345675",
                    "customs_status": "pre_cleared",
                    "priority": "express"
                }
            )
        ]
        
        for shipment in shipments:
            session.add(shipment)
        
        await session.commit()
        print(f"✅ {len(shipments)} shipments seeded")

async def seed_risks():
    """Seed sample risks"""
    async with AsyncSessionLocal() as session:
        # Get shipment IDs
        from sqlalchemy import select
        result = await session.execute(select(Shipment.id, Shipment.tracking_number))
        shipments = result.all()
        
        if not shipments:
            print("❌ No shipments found for risk seeding")
            return
        
        risks = []
        for shipment_id, tracking_number in shipments[:2]:  # Add risks to first 2 shipments
            risks.extend([
                Risk(
                    shipment_id=shipment_id,
                    risk_type=RiskType.PORT_CONGESTION.value,
                    severity=RiskSeverity.HIGH.value,
                    status=RiskStatus.DETECTED.value,
                    description=f"Port congestion detected for {tracking_number}",
                    confidence=0.85,
                    detected_at=datetime.utcnow() - timedelta(hours=6),
                    expected_delay_hours=24,
                    expected_cost_impact=5000,
                    affected_parties=["shipper", "consignee", "carrier"],
                    mitigation_actions=[
                        {"action": "reroute", "description": "Alternative port via Suez"},
                        {"action": "delay", "description": "Wait for congestion to clear"}
                    ],
                    selected_mitigation={"action": "reroute", "reason": "Faster overall"},
                    source="MCP Risk Detector",
                    risk_metadata={"port": "NLRTM", "congestion_level": 0.8}
                ),
                Risk(
                    shipment_id=shipment_id,
                    risk_type=RiskType.CUSTOMS_DELAY.value,
                    severity=RiskSeverity.MEDIUM.value,
                    status=RiskStatus.MITIGATING.value,
                    description=f"Customs documentation incomplete for {tracking_number}",
                    confidence=0.75,
                    detected_at=datetime.utcnow() - timedelta(hours=3),
                    expected_delay_hours=12,
                    expected_cost_impact=1500,
                    affected_parties=["shipper", "customs_broker"],
                    mitigation_actions=[
                        {"action": "expedite", "description": "Premium clearance service"},
                        {"action": "documents", "description": "Submit missing documents"}
                    ],
                    selected_mitigation={"action": "expedite", "reason": "Time critical"},
                    source="Customs API",
                    risk_metadata={"missing_docs": ["certificate_of_origin"]}
                )
            ])
        
        for risk in risks:
            session.add(risk)
        
        await session.commit()
        print(f"✅ {len(risks)} risks seeded")

async def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    await create_tables()
    await seed_shipments()
    await seed_risks()
    
    print("✅ Database seeding completed!")

if __name__ == "__main__":
    asyncio.run(main())
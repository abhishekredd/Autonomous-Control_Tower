import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.shipment import Shipment, ShipmentStatus, ShipmentMode, ShipmentEvent, ShipmentRoute
from app.models.risk import Risk, RiskType, RiskSeverity, RiskStatus
from app.models.simulation import Simulation, SimulationType, SimulationStatus
from app.services.shipment_service import ShipmentService
from app.services.risk_service import RiskService
import json

# Port database for realistic simulation
PORTS = {
    "asia": ["CNSHA", "CNNGB", "CNYTN", "SGSIN", "HKHKG", "JPTYO", "KRINC"],
    "europe": ["NLRTM", "DEHAM", "BEANR", "GBFXT", "FRLEH", "ESBCN"],
    "america": ["USLAX", "USLGB", "USNYC", "USORF", "CAMTR", "BRSSZ"],
    "middle_east": ["AEDXB", "AEJEA", "QAUDH", "OMSHJ"],
}

# Carrier database
CARRIERS = [
    "Maersk Line", "MSC", "COSCO Shipping", "CMA CGM", 
    "Hapag-Lloyd", "ONE", "Evergreen", "Yang Ming"
]

# Product types
PRODUCT_TYPES = [
    "electronics", "clothing", "machinery", "automotive", 
    "pharmaceutical", "food", "chemicals", "furniture"
]

# Shipper/Consignee database
COMPANIES = [
    "Global Electronics Inc.", "Fashion Forward Ltd.", "Auto Parts Co.",
    "Pharma Solutions", "Fresh Foods International", "Industrial Machinery Corp.",
    "Tech Components Ltd.", "Home Furnishings Group"
]

class SimulationDataGenerator:
    """Generate realistic simulation data"""
    
    def __init__(self):
        self.shipment_service = ShipmentService()
        self.risk_service = RiskService()
    
    async def create_tables(self):
        """Create database tables"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created")
    
    async def generate_realistic_shipments(self, count: int = 50):
        """Generate realistic shipment data"""
        shipments = []
        
        for i in range(count):
            # Generate realistic dates
            days_ago = random.randint(1, 90)
            departure_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Random transit time based on mode
            mode = random.choice(list(ShipmentMode))
            if mode == ShipmentMode.AIR:
                transit_days = random.randint(2, 7)
            elif mode == ShipmentMode.SEA:
                transit_days = random.randint(14, 45)
            else:
                transit_days = random.randint(7, 21)
            
            arrival_date = departure_date + timedelta(days=transit_days)
            
            # Determine status based on dates
            if arrival_date < datetime.utcnow():
                status = ShipmentStatus.ARRIVED
            elif departure_date > datetime.utcnow():
                status = ShipmentStatus.PENDING
            else:
                status = random.choice([
                    ShipmentStatus.IN_TRANSIT, 
                    ShipmentStatus.DELAYED, 
                    ShipmentStatus.IN_TRANSIT
                ])
            
            # Select random ports
            origin_region = random.choice(list(PORTS.keys()))
            dest_region = random.choice([r for r in PORTS.keys() if r != origin_region])
            
            origin_port = random.choice(PORTS[origin_region])
            dest_port = random.choice(PORTS[dest_region])
            
            # Generate realistic metadata
            metadata = {
                "container_number": f"CONT{random.randint(1000000, 9999999)}",
                "vessel": f"Vessel-{random.randint(100, 999)}",
                "product_type": random.choice(PRODUCT_TYPES),
                "insurance_value": round(random.uniform(1.1, 1.3), 2),  # 10-30% over value
                "customs_status": random.choice(["pre_cleared", "pending", "cleared"]),
                "quality_status": random.choice(["clear", "clear", "clear", "inspection"]),
                "temperature_controlled": random.choice([True, False]),
                "hazardous_material": random.choice([True, False, False, False]),
                "special_handling": random.choice(["none", "fragile", "oversized", "perishable"])
            }
            
            shipment = Shipment(
                tracking_number=f"TRK{800000 + i:06d}",
                reference_number=f"SH-{100 + i:03d}",
                origin=f"{origin_port} Port",
                destination=f"{dest_port} Port",
                current_location=self._generate_current_location(status, departure_date, arrival_date),
                current_port=self._get_current_port(status, origin_port, dest_port),
                next_port=dest_port if status == ShipmentStatus.IN_TRANSIT else None,
                status=status,
                mode=mode,
                weight=round(random.uniform(1000, 50000), 2),
                volume=round(random.uniform(10, 200), 2),
                value=round(random.uniform(50000, 1000000), 2),
                estimated_departure=departure_date,
                estimated_arrival=arrival_date,
                actual_departure=departure_date if departure_date < datetime.utcnow() else None,
                actual_arrival=arrival_date if arrival_date < datetime.utcnow() else None,
                shipper=random.choice(COMPANIES),
                carrier=random.choice(CARRIERS),
                consignee=random.choice(COMPANIES),
                customs_broker=f"Customs Broker {random.randint(1, 20)}",
                is_at_risk=random.choice([True, False, False]),  # 33% at risk
                risk_score=round(random.uniform(0, 0.9), 2) if random.choice([True, False]) else 0.0,
                last_risk_check=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                metadata=metadata
            )
            
            shipments.append(shipment)
        
        return shipments
    
    def _generate_current_location(self, status, departure, arrival):
        """Generate realistic current location"""
        if status == ShipmentStatus.PENDING:
            return "At origin port"
        elif status == ShipmentStatus.ARRIVED:
            return "At destination port"
        elif status == ShipmentStatus.DELAYED:
            return random.choice([
                "Held at intermediate port",
                "Waiting for customs clearance",
                "Weather delay in transit"
            ])
        else:  # IN_TRANSIT
            progress = (datetime.utcnow() - departure) / (arrival - departure)
            if progress < 0.3:
                return "Pacific Ocean" if random.choice([True, False]) else "Indian Ocean"
            elif progress < 0.7:
                return "Mid-Atlantic" if random.choice([True, False]) else "Mediterranean Sea"
            else:
                return "Approaching destination"
    
    def _get_current_port(self, status, origin, destination):
        """Get current port based on status"""
        if status == ShipmentStatus.PENDING:
            return origin
        elif status == ShipmentStatus.ARRIVED:
            return destination
        elif status == ShipmentStatus.IN_TRANSIT:
            # Sometimes at intermediate port
            return random.choice([None, "SGSIN", "AEDXB", "USLAX"])
        return None
    
    async def generate_risks_for_shipments(self, shipments):
        """Generate realistic risks for shipments"""
        risks = []
        
        for shipment in shipments:
            if not shipment.is_at_risk:
                continue
            
            # Determine number of risks (1-3)
            num_risks = random.randint(1, 3)
            
            for _ in range(num_risks):
                risk_type = random.choice(list(RiskType))
                severity = random.choice(list(RiskSeverity))
                
                risk = Risk(
                    shipment_id=shipment.id,
                    risk_type=risk_type,
                    severity=severity,
                    status=random.choice([
                        RiskStatus.DETECTED, 
                        RiskStatus.ANALYZING, 
                        RiskStatus.MITIGATING,
                        RiskStatus.RESOLVED
                    ]),
                    description=self._generate_risk_description(risk_type, severity, shipment),
                    confidence=round(random.uniform(0.5, 0.95), 2),
                    detected_at=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                    resolved_at=datetime.utcnow() if random.choice([True, False]) else None,
                    expected_delay_hours=round(random.uniform(6, 72), 1),
                    expected_cost_impact=round(random.uniform(1000, 20000), 2),
                    affected_parties=random.sample(["shipper", "consignee", "carrier", "customs_broker"], 
                                                  random.randint(1, 3)),
                    mitigation_actions=self._generate_mitigation_actions(risk_type),
                    selected_mitigation=random.choice([None, {"action": "reroute", "reason": "avoid congestion"}]),
                    source=random.choice(["MCP Agent", "System", "External API", "Manual"]),
                    metadata=self._generate_risk_metadata(risk_type, shipment)
                )
                
                risks.append(risk)
        
        return risks
    
    def _generate_risk_description(self, risk_type, severity, shipment):
        """Generate realistic risk description"""
        descriptions = {
            RiskType.PORT_CONGESTION: [
                f"Port congestion at {shipment.next_port or 'next port'}. Wait time: {random.randint(12, 72)} hours.",
                f"Vessel backlog at {shipment.next_port or 'destination port'}. Berthing delay expected."
            ],
            RiskType.CUSTOMS_DELAY: [
                "Customs documentation incomplete. Additional verification required.",
                "Import license pending approval. Customs clearance delayed."
            ],
            RiskType.QUALITY_HOLD: [
                "Random quality inspection selected by port authorities.",
                "Product sample sent for laboratory testing. Hold until results."
            ],
            RiskType.WEATHER_IMPACT: [
                "Storm system detected along route. Vessel rerouting necessary.",
                "Heavy fog at destination port. Berthing operations suspended."
            ],
            RiskType.EQUIPMENT_FAILURE: [
                "Refrigeration unit malfunction detected. Temperature control compromised.",
                "Container handling equipment failure at intermediate port."
            ]
        }
        
        base_desc = descriptions.get(risk_type, [f"{risk_type.value.replace('_', ' ').title()} detected."])[0]
        return f"[{severity.value.upper()}] {base_desc}"
    
    def _generate_mitigation_actions(self, risk_type):
        """Generate mitigation actions for risk type"""
        actions_map = {
            RiskType.PORT_CONGESTION: [
                {"action": "reroute", "description": "Alternative port via different route"},
                {"action": "delay", "description": "Wait for congestion to clear"},
                {"action": "expedite", "description": "Priority berthing arrangement"}
            ],
            RiskType.CUSTOMS_DELAY: [
                {"action": "expedite_documents", "description": "Express documentation service"},
                {"action": "local_agent", "description": "Engage local customs broker"},
                {"action": "pre_clearance", "description": "Advance customs clearance"}
            ],
            RiskType.QUALITY_HOLD: [
                {"action": "remote_inspection", "description": "Virtual inspection via video"},
                {"action": "expedite_testing", "description": "Priority laboratory testing"},
                {"action": "alternative_documentation", "description": "Provide additional certifications"}
            ]
        }
        
        return actions_map.get(risk_type, [{"action": "monitor", "description": "Monitor situation"}])
    
    def _generate_risk_metadata(self, risk_type, shipment):
        """Generate risk metadata"""
        metadata = {
            "detected_by": random.choice(["AI Model", "System Alert", "Manual Report"]),
            "confidence_score": round(random.uniform(0.6, 0.95), 2),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        if risk_type == RiskType.PORT_CONGESTION:
            metadata.update({
                "port": shipment.next_port or shipment.destination,
                "congestion_level": round(random.uniform(0.6, 0.95), 2),
                "estimated_wait_hours": random.randint(12, 72),
                "alternative_ports": random.sample(list(PORTS.values())[0], 2)
            })
        elif risk_type == RiskType.WEATHER_IMPACT:
            metadata.update({
                "weather_system": random.choice(["Storm", "Typhoon", "Fog", "High Winds"]),
                "affected_area": random.choice(["Pacific Ocean", "Atlantic Ocean", "Indian Ocean"]),
                "severity": random.choice(["Moderate", "Severe", "Extreme"]),
                "duration_hours": random.randint(12, 48)
            })
        
        return metadata
    
    async def generate_shipment_events(self, shipments):
        """Generate timeline events for shipments"""
        events = []
        
        for shipment in shipments:
            # Base events
            event_types = [
                ("created", "Shipment created in system", shipment.origin),
                ("documentation_complete", "All documentation submitted", shipment.origin),
                ("departed", f"Departed {shipment.origin}", shipment.origin),
                ("in_transit", "Vessel in transit", "At sea")
            ]
            
            if shipment.status == ShipmentStatus.ARRIVED:
                event_types.extend([
                    ("arrived", f"Arrived at {shipment.destination}", shipment.destination),
                    ("customs_cleared", "Customs clearance completed", shipment.destination),
                    ("available_for_pickup", "Ready for consignee pickup", shipment.destination)
                ])
            elif shipment.status == ShipmentStatus.DELAYED:
                event_types.append(
                    ("delayed", "Shipment delayed due to unforeseen circumstances", "In transit")
                )
            
            # Add random intermediate events
            if shipment.mode == ShipmentMode.SEA:
                intermediate_ports = random.sample(
                    ["Singapore", "Dubai", "Suez Canal", "Panama Canal", "Colombo"], 
                    random.randint(1, 3)
                )
                for port in intermediate_ports:
                    event_types.append(
                        ("port_call", f"Port call at {port}", port)
                    )
            
            # Create events with realistic timestamps
            start_time = shipment.estimated_departure
            end_time = shipment.estimated_arrival
            
            for i, (event_type, description, location) in enumerate(event_types):
                if start_time and end_time:
                    # Distribute events along timeline
                    progress = i / len(event_types)
                    event_time = start_time + (end_time - start_time) * progress
                else:
                    event_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                
                event = ShipmentEvent(
                    shipment_id=shipment.id,
                    event_type=event_type,
                    location=location,
                    description=description,
                    timestamp=event_time,
                    metadata={
                        "event_sequence": i + 1,
                        "automated": random.choice([True, False])
                    }
                )
                
                events.append(event)
        
        return events
    
    async def seed_all_data(self):
        """Seed all simulation data"""
        print("🌱 Starting comprehensive data seeding...")
        
        # Create tables
        await self.create_tables()
        
        async with AsyncSessionLocal() as session:
            # Generate and save shipments
            print("📦 Generating realistic shipments...")
            shipments = await self.generate_realistic_shipments(50)
            
            for shipment in shipments:
                session.add(shipment)
            
            await session.commit()
            print(f"✅ {len(shipments)} shipments created")
            
            # Refresh to get IDs
            await session.flush()
            
            # Generate risks
            print("⚠️ Generating risks...")
            risks = await self.generate_risks_for_shipments(shipments)
            
            for risk in risks:
                session.add(risk)
            
            await session.commit()
            print(f"✅ {len(risks)} risks created")
            
            # Generate events
            print("📅 Generating shipment events...")
            events = await self.generate_shipment_events(shipments)
            
            for event in events:
                session.add(event)
            
            await session.commit()
            print(f"✅ {len(events)} shipment events created")
            
            # Generate some simulations
            print("🔮 Generating simulation data...")
            for shipment in shipments[:10]:  # Create simulations for first 10 shipments
                if shipment.is_at_risk:
                    simulation = Simulation(
                        shipment_id=shipment.id,
                        simulation_type=random.choice(list(SimulationType)),
                        status=random.choice([SimulationStatus.COMPLETED, SimulationStatus.FAILED]),
                        parameters={
                            "risk_type": "port_congestion",
                            "scenario": "mitigation_analysis"
                        },
                        scenario_description=f"What-if analysis for {shipment.tracking_number}",
                        results={
                            "alternatives": [
                                {"action": "reroute", "score": 0.85},
                                {"action": "delay", "score": 0.45}
                            ],
                            "best_option": {"action": "reroute", "reason": "Time savings"}
                        },
                        best_option={"action": "reroute", "confidence": 0.85},
                        confidence_score=round(random.uniform(0.6, 0.95), 2),
                        initiated_by=random.choice(["MCP Agent", "System", "User"]),
                        execution_time=round(random.uniform(1.5, 10.0), 2),
                        metadata={"simulation_version": "1.0", "model_used": "digital_twin_v2"}
                    )
                    session.add(simulation)
            
            await session.commit()
            print("✅ Simulation data created")
        
        print("🎉 Comprehensive data seeding completed!")
        
        # Print summary
        await self.print_data_summary()
    
    async def print_data_summary(self):
        """Print summary of seeded data"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            # Shipment summary
            result = await session.execute(
                select(func.count(Shipment.id))
            )
            total_shipments = result.scalar()
            
            result = await session.execute(
                select(func.count(Shipment.id)).where(Shipment.is_at_risk == True)
            )
            at_risk_shipments = result.scalar()
            
            # Risk summary
            result = await session.execute(
                select(func.count(Risk.id))
            )
            total_risks = result.scalar()
            
            result = await session.execute(
                select(func.count(Risk.id)).where(Risk.severity == RiskSeverity.HIGH)
            )
            high_risks = result.scalar()
            
            # Event summary
            result = await session.execute(
                select(func.count(ShipmentEvent.id))
            )
            total_events = result.scalar()
            
            print("\n" + "="*50)
            print("📊 DATA SEEDING SUMMARY")
            print("="*50)
            print(f"📦 Shipments: {total_shipments} total, {at_risk_shipments} at risk")
            print(f"⚠️  Risks: {total_risks} total, {high_risks} high severity")
            print(f"📅 Events: {total_events} timeline events")
            print(f"🔮 Simulations: Generated for high-risk shipments")
            print("="*50)
            print("\n✅ Database is ready with realistic simulation data!")
            print("\n💡 Sample API endpoints to test:")
            print("   GET  http://localhost:8000/api/v1/shipments/")
            print("   GET  http://localhost:8000/api/v1/risks/")
            print("   GET  http://localhost:8000/api/v1/simulations/")
            print("\n🚀 Access API documentation at: http://localhost:8000/docs")

async def main():
    """Main function to run enhanced data seeding"""
    generator = SimulationDataGenerator()
    await generator.seed_all_data()

if __name__ == "__main__":
    asyncio.run(main())
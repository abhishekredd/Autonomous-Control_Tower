import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from sqlalchemy import select

from app.core.redis import redis_client
from app.core.database import AsyncSessionLocal
from app.models.shipment import Shipment, ShipmentStatus
from app.models.risk import Risk, RiskType, RiskSeverity, RiskStatus
from app.services.risk_service import RiskService
from app.services.simulation_service import SimulationService
from app.services.action_service import ActionService
from app.services.communication_service import CommunicationService

class CentralOrchestrator:
    """
    Central agent that watches end-to-end shipments, detects risks,
    simulates mitigation options, executes actions, and coordinates communication.
    """
    
    def __init__(self):
        self.risk_service = RiskService()
        self.simulation_service = SimulationService()
        self.action_service = ActionService()
        self.communication_service = CommunicationService()
        
        # Active monitoring tasks
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.active_shipments: Dict[int, Dict] = {}
        
        # Configuration
        self.monitoring_interval = 30  # seconds
        self.risk_check_interval = 60  # seconds
        self.reporting_interval = 300  # seconds
        
        # PubSub object
        self.pubsub = redis_client.pubsub()
    async def initialize(self):
        """Initialize the orchestrator"""
        print("🚀 Initializing Central Orchestrator...")
        
        # Subscribe to Redis channels via pubsub
        await self.pubsub.subscribe(
            "shipment_created",
            "shipment_updated",
            "risk_detected",
            "action_completed"
        )
        
        # Load active shipments
        await self._load_active_shipments()
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        # Start risk assessment loop
        asyncio.create_task(self._risk_assessment_loop())
        
        print("✅ Central Orchestrator initialized")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for all shipments"""
        while True:
            try:
                # Check each active shipment
                for shipment_id, shipment_data in self.active_shipments.items():
                    await self._monitor_shipment(shipment_id, shipment_data)
                
                # Process Redis messages
                await self._process_redis_messages()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    async def _risk_assessment_loop(self):
        """Periodic risk assessment loop"""
        while True:
            try:
                # Check for new risks on all shipments
                await self._assess_all_shipments_risks()
                
                # Update risk scores
                await self._update_risk_scores()
                
                await asyncio.sleep(self.risk_check_interval)
                
            except Exception as e:
                print(f"Risk assessment loop error: {e}")
                await asyncio.sleep(10)
    async def _monitor_shipment(self, shipment_id: int, shipment_data: Dict):
        """Monitor a single shipment for issues"""
        try:
            # Check for delays
            await self._check_delays(shipment_id, shipment_data)
            
            # Check location updates
            await self._check_location(shipment_id, shipment_data)
            
            # Check for congestion at next port
            if shipment_data.get("next_port"):
                await self._check_port_congestion(shipment_id, shipment_data["next_port"])
            
            # Check customs status
            await self._check_customs_status(shipment_id, shipment_data)
            
            # Check quality holds
            await self._check_quality_holds(shipment_id, shipment_data)
            
        except Exception as e:
            print(f"Error monitoring shipment {shipment_id}: {e}")

    async def _check_delays(self, shipment_id: int, shipment_data: Dict):
        """Check if shipment is delayed"""
        eta = shipment_data.get("estimated_arrival")
        if eta and datetime.utcnow() > eta:
            delay_hours = (datetime.utcnow() - eta).total_seconds() / 3600
            
            if delay_hours > 4:  # Threshold for delay risk
                await self._create_risk(
                    shipment_id=shipment_id,
                    risk_type=RiskType.OTHER,
                    severity=RiskSeverity.HIGH if delay_hours > 24 else RiskSeverity.MEDIUM,
                    description=f"Shipment delayed by {delay_hours:.1f} hours",
                    confidence=min(0.9, delay_hours / 48),
                    metadata={"delay_hours": delay_hours}
                )

    async def _check_location(self, shipment_id: int, shipment_data: Dict):
        """Check if shipment location has changed or deviated"""
        current_loc = shipment_data.get("current_location")
        next_port = shipment_data.get("next_port")
        destination = shipment_data.get("destination")

        if not current_loc:
            shipment_data["current_location"] = shipment_data.get("origin", "unknown")
            return

        # Example deviation check
        if next_port and current_loc != next_port:
                await self._create_risk(
                shipment_id=shipment_id,
                risk_type=RiskType.OTHER,
                severity=RiskSeverity.MEDIUM,
                description=f"Shipment {shipment_id} deviated from expected route. Current: {current_loc}, Expected: {next_port}",
                confidence=0.7,
                metadata={"current_location": current_loc, "expected_next_port": next_port}
            )

        # Arrival check
        if destination and current_loc == destination:
            print(f"✅ Shipment {shipment_id} has arrived at destination {destination}")

    async def _check_port_congestion(self, shipment_id: int, port_code: str):
        """Check for port congestion"""
        congestion_level = await self._get_port_congestion_level(port_code)
        
        if congestion_level > 0.7:  # High congestion threshold
            await self._create_risk(
                shipment_id=shipment_id,
                risk_type=RiskType.PORT_CONGESTION,
                severity=RiskSeverity.HIGH if congestion_level > 0.8 else RiskSeverity.MEDIUM,
                description=f"Port congestion at {port_code}",
                confidence=congestion_level,
                metadata={
                    "port": port_code,
                    "congestion_level": congestion_level,
                    "estimated_wait_hours": congestion_level * 48
                }
            )

    async def _check_customs_status(self, shipment_id: int, shipment_data: Dict):
        """Check customs clearance status"""
        customs_status = shipment_data.get("customs_status")
        
        if customs_status in ["held", "delayed", "under_review"]:
            await self._create_risk(
                shipment_id=shipment_id,
                risk_type=RiskType.CUSTOMS_DELAY,
                severity=RiskSeverity.HIGH,
                description=f"Customs clearance {customs_status}",
                confidence=0.85,
                metadata={"customs_status": customs_status}
            )

    async def _check_quality_holds(self, shipment_id: int, shipment_data: Dict):
        """Check for quality inspection holds"""
        quality_status = shipment_data.get("quality_status")
        
        if quality_status in ["hold", "inspection"]:
            await self._create_risk(
                shipment_id=shipment_id,
                risk_type=RiskType.QUALITY_HOLD,
                severity=RiskSeverity.MEDIUM,
                description="Quality inspection hold",
                confidence=0.9,
                metadata={"quality_status": quality_status}
            )
    async def _create_risk(self, shipment_id: int, risk_type: RiskType,
                          severity: RiskSeverity, description: str,
                          confidence: float, metadata: Dict):
        """Create a new risk record"""
        async with AsyncSessionLocal() as session:
            # Normalize risk_type robustly: accept enum member, name or value
            try:
                if isinstance(risk_type, RiskType):
                    rt = risk_type
                elif isinstance(risk_type, str):
                    # Try name lookup first (e.g., 'CUSTOMS_DELAY')
                    try:
                        rt = RiskType[risk_type]
                    except KeyError:
                        # Try construction by value (e.g., 'customs_delay')
                        try:
                            rt = RiskType(risk_type)
                        except Exception:
                            rt = RiskType.OTHER
                else:
                    rt = RiskType.OTHER
            except Exception:
                rt = RiskType.OTHER

            # Normalize values to store enum .value strings (lowercase) to match DB enum labels
            rt_val = rt.value if isinstance(rt, RiskType) else (str(rt) if rt else RiskType.OTHER.value)
            if isinstance(severity, RiskSeverity):
                sev_val = severity.value
            else:
                try:
                    sev_val = RiskSeverity[severity].value
                except Exception:
                    try:
                        sev_val = RiskSeverity(severity).value
                    except Exception:
                        sev_val = RiskSeverity.MEDIUM.value

            risk = Risk(
                shipment_id=shipment_id,
                risk_type=rt_val,
                severity=sev_val,
                description=description,
                confidence=confidence,
                detected_at=datetime.utcnow(),
                status=RiskStatus.DETECTED.value,
                risk_metadata=metadata
            )

            session.add(risk)
            try:
                await session.commit()
            except Exception as exc:
                await session.rollback()
                # Log detailed context for debugging enum/DB mapping issues
                print(f"[ERROR] Failed to commit new risk for shipment={shipment_id} risk_type_raw={risk_type} resolved_rt={getattr(rt,'name',str(rt))} exception={exc}")
                raise

            # Update shipment risk flag
            shipment = await session.get(Shipment, shipment_id)
            if shipment:
                shipment.is_at_risk = True
                shipment.risk_score = max(shipment.risk_score, confidence)
                shipment.last_risk_check = datetime.utcnow()
                await session.commit()

            # Publish risk event
            await redis_client.publish(
                "risk_detected",
                json.dumps({
                    "shipment_id": shipment_id,
                    "risk_id": risk.id,
                    "risk_type": getattr(rt, "value", str(rt)),
                    "severity": getattr(severity, "value", str(severity)),
                    "description": description
                })
            )

            # Start mitigation process
            await self._handle_new_risk(risk.id, shipment_id)
    
    async def _handle_new_risk(self, risk_id: int, shipment_id: int):
        """Handle a newly detected risk"""
        print(f"⚠️ Handling new risk {risk_id} for shipment {shipment_id}")
        
        # Step 1: Simulate mitigation options
        simulation_results = await self.simulation_service.simulate_mitigations(
            shipment_id=shipment_id,
            risk_id=risk_id
        )
        
        # Step 2: Select best option
        best_option = self._select_best_mitigation(simulation_results)
        
        # Step 3: Execute action if confidence is high
        if best_option.get("confidence", 0) > 0.7:
            action_result = await self.action_service.execute_action(
                shipment_id=shipment_id,
                action_type=best_option["action_type"],
                parameters=best_option["parameters"]
            )
            
            # Step 4: Notify stakeholders
            await self.communication_service.notify_stakeholders(
                shipment_id=shipment_id,
                risk_id=risk_id,
                action_taken=best_option["action_type"],
                action_result=action_result
            )
        else:
            # Escalate to human operator
            await self._escalate_to_human(shipment_id, risk_id, simulation_results)
    
    def _select_best_mitigation(self, simulations: List[Dict]) -> Dict:
        """Select the best mitigation option from simulations"""
        if not simulations:
            return {}
        
        # Simple selection based on confidence score
        return max(simulations, key=lambda x: x.get("confidence", 0))
    
    async def _escalate_to_human(self, shipment_id: int, risk_id: int,
                               simulations: List[Dict]):
        """Escalate decision to human operator"""
        print(f"🚨 Escalating risk {risk_id} for shipment {shipment_id} to human operator")
        # TODO: implement escalation workflow (e.g., notify via email, dashboard alert)
    async def _process_redis_messages(self):
        """Process incoming Redis PubSub messages"""
        try:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                data = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
                print(f"📨 Redis message on {channel}: {data}")
                # TODO: route to appropriate handler (shipment_created, shipment_updated, etc.)
        except Exception as e:
            print(f"Redis processing error: {e}")

    async def _assess_all_shipments_risks(self):
        """Run risk assessment across all active shipments"""
        for shipment_id, shipment_data in self.active_shipments.items():
            try:
                async with AsyncSessionLocal() as session:
                    risks = await self.risk_service.assess_shipment(shipment_id, session)
                    if risks:
                        print(f"Assessed risks for shipment {shipment_id}: {len(risks)} risks detected")
            except Exception as e:
                print(f"Risk assessment error for shipment {shipment_id}: {e}")

    async def _update_risk_scores(self):
        """Update risk scores for shipments in DB"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Shipment))
            shipments = result.scalars().all()
            for shipment in shipments:
                risks = await session.execute(
                    select(Risk).where(Risk.shipment_id == shipment.id)
                )
                risks = risks.scalars().all()
                if risks:
                        shipment.risk_score = max(r.confidence for r in risks)
                        shipment.is_at_risk = any((getattr(r.status, "value", str(r.status))).lower() == RiskStatus.DETECTED.value for r in risks)
            await session.commit()

    async def _load_active_shipments(self):
        """Load active shipments from the database into memory"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Shipment).where(Shipment.status == ShipmentStatus.IN_TRANSIT)
            )
            shipments = result.scalars().all()

            for shipment in shipments:
                self.active_shipments[shipment.id] = {
                    "shipment": shipment,
                    "last_checked": datetime.utcnow(),
                }

        print(f"📦 Loaded {len(self.active_shipments)} active shipments")

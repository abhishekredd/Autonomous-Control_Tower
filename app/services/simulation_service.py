from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.simulation import Simulation, SimulationType, SimulationStatus
from app.models.shipment import Shipment
from app.models.risk import Risk
from app.schemas.simulation import SimulationCreate
from app.services.risk_service import RiskService

class SimulationService:
    """Service for running simulations and what-if analysis"""

    # ------------------------------
    # Queries
    # ------------------------------

    async def get_shipment_simulations(self, shipment_id: int, session: AsyncSession) -> List[Simulation]:
        """Return all simulations for a given shipment"""
        stmt = select(Simulation).where(Simulation.shipment_id == shipment_id).order_by(Simulation.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_simulation(self, simulation_id: int, session: AsyncSession) -> Optional[Simulation]:
        """Return single simulation"""
        return await session.get(Simulation, simulation_id)
    async def create_simulation(self, simulation: SimulationCreate, session: AsyncSession) -> Simulation:
        print(f"[DEBUG] Creating simulation for shipment {simulation.shipment_id} type={simulation.simulation_type}")
        """Create a new simulation record from SimulationCreate schema"""
        # Normalize simulation_type coming from Pydantic schema to the model enum
        try:
            stype_value = getattr(simulation.simulation_type, "value", str(simulation.simulation_type))
        except Exception:
            stype_value = str(simulation.simulation_type)

        # Some enum objects may be represented as Enum members from a different class
        # Normalize to the value string then try to construct the model enum by value,
        # falling back to lookup by name.
        if isinstance(stype_value, str) and stype_value.startswith("SimulationType."):
            # handle repr like 'SimulationType.MITIGATION_ANALYSIS'
            stype_value = stype_value.split(".")[-1]

        try:
            stype = SimulationType(stype_value)
        except ValueError:
            try:
                stype = SimulationType[stype_value.upper()]
            except Exception as exc:
                raise

        sim = Simulation(
            shipment_id=simulation.shipment_id,
            simulation_type=stype,
            parameters=simulation.parameters,
            status=SimulationStatus.PENDING,
            initiated_by="system",
            scenario_description=simulation.scenario_description,
        )
        session.add(sim)
        await session.commit()
        await session.refresh(sim)
        print(f"[DEBUG] Simulation {sim.id} created successfully")
        return sim
    async def simulate_mitigations(self, shipment_id: int, risk_id: int) -> List[Dict]:
        """Simulate various mitigation options for a risk"""
        simulations: List[Dict] = []

        async with AsyncSessionLocal() as session:
            risk = await session.get(Risk, risk_id)
            shipment = await session.get(Shipment, shipment_id)
            if not risk or not shipment:
                return simulations

            scenarios = self._generate_mitigation_scenarios(risk, shipment)
            for scenario in scenarios:
                result = await self._run_simulation(scenario, risk, shipment)
                simulations.append(result)

        return simulations

    def _generate_mitigation_scenarios(self, risk: Risk, shipment: Shipment) -> List[Dict]:
        """Generate mitigation scenarios based on risk type"""
        scenarios: List[Dict] = []
        rtype = risk.risk_type.value if hasattr(risk.risk_type, "value") else str(risk.risk_type)

        if rtype == "port_congestion":
            scenarios = [
                {
                    "name": "Alternative Port",
                    "action_type": "reroute",
                    "parameters": {
                        "alternative_port": self._get_alternative_port(shipment.next_port),
                        "estimated_time_savings": 24,
                        "cost_impact": 5000,
                    },
                },
                {
                    "name": "Schedule Adjustment",
                    "action_type": "delay",
                    "parameters": {
                        "delay_hours": 12,
                        "estimated_time_savings": 12,
                        "cost_impact": 1000,
                        "reason": "Avoid peak congestion",
                    },
                },
            ]
        elif rtype == "customs_delay":
            scenarios = [
                {
                    "name": "Expedited Clearance",
                    "action_type": "expedite_customs",
                    "parameters": {
                        "service_level": "premium",
                        "estimated_time_savings": 20,
                        "cost_impact": 2500,
                    },
                },
                {
                    "name": "Additional Documentation",
                    "action_type": "submit_documents",
                    "parameters": {
                        "document_types": ["certificate_of_origin", "commercial_invoice"],
                        "estimated_time_savings": 12,
                        "cost_impact": 500,
                    },
                },
            ]
        elif rtype == "quality_hold":
            scenarios = [
                {
                    "name": "Remote Inspection",
                    "action_type": "remote_inspection",
                    "parameters": {
                        "inspection_type": "video",
                        "estimated_time_savings": 18,
                        "cost_impact": 1500,
                    },
                },
                {
                    "name": "Alternative Batch",
                    "action_type": "source_alternative",
                    "parameters": {
                        "source_location": "nearby_warehouse",
                        "estimated_time_savings": 24,
                        "cost_impact": 3000,
                    },
                },
            ]
        else:
            scenarios = [
                {
                    "name": "Expedite Leg",
                    "action_type": "expedite_leg",
                    "parameters": {
                        "estimated_time_savings": 8,
                        "cost_impact": 1200,
                    },
                }
            ]
        return scenarios
    async def _run_simulation(self, scenario: Dict, risk: Risk, shipment: Shipment) -> Dict:
        """Run a single simulation scenario"""
        await asyncio.sleep(0.3)  # simulate compute time

        est_savings = scenario["parameters"].get("estimated_time_savings", 0)
        cost_impact = scenario["parameters"].get("cost_impact", 0)
        time_score = min(1.0, est_savings / 48)
        cost_score = max(0.0, 1.0 - (cost_impact / 10000.0))
        risk_reduction = 0.7

        confidence = (time_score * 0.4) + (cost_score * 0.3) + (risk_reduction * 0.3)

        return {
            "scenario_name": scenario["name"],
            "action_type": scenario["action_type"],
            "parameters": scenario["parameters"],
            "time_savings_hours": est_savings,
            "cost_impact": cost_impact,
            "risk_reduction": risk_reduction,
            "confidence": confidence,
            "feasibility": 0.8,
            "implementation_time_hours": 2,
        }

    def _get_alternative_port(self, port_code: Optional[str]) -> str:
        """Get alternative port for congestion mitigation"""
        alternatives = {
            "CNSHA": "CNNGB",
            "USLAX": "USLGB",
            "NLRTM": "BEANR",
            "SGSIN": "MYPKG",
        }
        return alternatives.get(port_code, "ALT001")

    async def update_simulation_results(self, simulation_id: int, results: Dict, session: AsyncSession) -> Optional[Simulation]:
        """Update simulation results"""
        sim = await session.get(Simulation, simulation_id)
        if not sim:
            return None

        sim.status = SimulationStatus.COMPLETED
        sim.results = results
        if hasattr(sim, "created_at") and sim.created_at:
            # sim.created_at is timezone-aware (DB uses timezone=True). Use timezone-aware now
            now = datetime.now(timezone.utc)
            # If created_at is naive, coerce to UTC naive for subtraction; otherwise ensure both are aware
            try:
                sim_created = sim.created_at
                if sim_created.tzinfo is None:
                    sim_created = sim_created.replace(tzinfo=timezone.utc)
                sim.execution_time = (now - sim_created).total_seconds()
            except Exception:
                # Fallback to best-effort using naive UTC
                sim.execution_time = (datetime.utcnow() - (sim.created_at if sim.created_at else datetime.utcnow())).total_seconds()

        sims = results.get("simulations")
        if isinstance(sims, list) and sims:
            best_option = max(sims, key=lambda x: x.get("confidence", 0))
            sim.best_option = best_option
            sim.confidence_score = best_option.get("confidence", 0)

        await session.commit()
        await session.refresh(sim)
        return sim
    
    async def run_simulation_task(self, simulation_id: int, parameters: Dict):
        print(f"[DEBUG] Running simulation task for id={simulation_id} with parameters={parameters}")
        """Background task to run a simulation and update results"""
        async with AsyncSessionLocal() as session:
            risk_service = RiskService()

            # Run risk assessment for the shipment
            shipment_id = parameters.get("shipment_id")
            detected_risks = []
            if shipment_id:
                detected_risks = await risk_service.assess_shipment(shipment_id, session)
                print(f"[DEBUG] Detected {len(detected_risks)} risks for shipment {shipment_id}")

            # Build results payload
            results = {
                "simulations": [
                    {
                        "scenario_name": "Risk Check",
                        "action_type": "analysis",
                        "parameters": parameters,
                        "confidence": 0.85,
                        "risk_reduction": 0.7,
                        "feasibility": 0.9,
                        "implementation_time_hours": 1,
                        "detected_risks": [r.id for r in detected_risks],
                    }
                ]
            }

            await self.update_simulation_results(simulation_id, results, session)
            print(f"[DEBUG] Simulation {simulation_id} updated with results")

    async def run_mitigation_simulation(self, simulation_id: int, shipment_id: int, risk_data: Dict):
        """Specific background task for running mitigation simulations for a single risk."""
        print(f"[DEBUG] Running mitigation simulation task id={simulation_id} shipment={shipment_id} risk_data={risk_data}")
        async with AsyncSessionLocal() as session:
            # load shipment
            shipment = await session.get(Shipment, shipment_id)
            if not shipment:
                print(f"[DEBUG] Shipment {shipment_id} not found for mitigation simulation")
                return

            # Normalize risk_type into Risk model enum (best-effort)
            from app.models.risk import Risk as RiskModel, RiskType as RiskModelType

            rt_raw = str(risk_data.get("risk_type") or "").strip()
            try:
                # Try by value (case-insensitive)
                rt = RiskModelType(rt_raw.lower()) if rt_raw else RiskModelType.OTHER
            except Exception:
                try:
                    rt = RiskModelType[rt_raw.upper()]
                except Exception:
                    rt = RiskModelType.OTHER

            # Build a lightweight Risk-like object for scenario generation
            # store risk_type as value string to match DB enum labels
            rt_val = rt.value if hasattr(rt, "value") else str(rt)
            fake_risk = RiskModel(
                shipment_id=shipment_id,
                risk_type=rt_val,
                severity=(risk_data.get("severity") or None),
                description=risk_data.get("description", "Mitigation analysis"),
                confidence=risk_data.get("confidence", 0.5),
                detected_at=datetime.now(timezone.utc),
            )

            # Generate scenarios and run simulations
            scenarios = self._generate_mitigation_scenarios(fake_risk, shipment)
            sims_results = []
            for scenario in scenarios:
                res = await self._run_simulation(scenario, fake_risk, shipment)
                sims_results.append(res)

            results = {"simulations": sims_results}
            await self.update_simulation_results(simulation_id, results, session)
            print(f"[DEBUG] Mitigation simulation {simulation_id} updated with {len(sims_results)} scenarios")
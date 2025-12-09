from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.simulation import Simulation, SimulationType, SimulationStatus
from app.models.shipment import Shipment
from app.models.risk import Risk

class SimulationService:
    """Service for running simulations and what-if analysis"""
    
    async def simulate_mitigations(self, shipment_id: int, risk_id: int) -> List[Dict]:
        """Simulate various mitigation options for a risk"""
        simulations = []
        
        # Get risk details
        async with AsyncSessionLocal() as session:
            risk = await session.get(Risk, risk_id)
            shipment = await session.get(Shipment, shipment_id)
            
            if not risk or not shipment:
                return simulations
            
            # Run different simulation scenarios
            scenarios = self._generate_mitigation_scenarios(risk, shipment)
            
            for scenario in scenarios:
                result = await self._run_simulation(scenario, risk, shipment)
                simulations.append(result)
        
        return simulations
    
    def _generate_mitigation_scenarios(self, risk: Risk, shipment: Shipment) -> List[Dict]:
        """Generate mitigation scenarios based on risk type"""
        scenarios = []
        
        if risk.risk_type == "port_congestion":
            scenarios = [
                {
                    "name": "Alternative Port",
                    "action_type": "reroute",
                    "parameters": {
                        "alternative_port": self._get_alternative_port(shipment.next_port),
                        "estimated_time_savings": 24,
                        "cost_impact": 5000
                    }
                },
                {
                    "name": "Schedule Adjustment",
                    "action_type": "delay",
                    "parameters": {
                        "delay_hours": 12,
                        "cost_impact": 1000,
                        "reason": "Avoid peak congestion"
                    }
                }
            ]
        
        elif risk.risk_type == "customs_delay":
            scenarios = [
                {
                    "name": "Expedited Clearance",
                    "action_type": "expedite_customs",
                    "parameters": {
                        "service_level": "premium",
                        "estimated_time_savings": 20,
                        "cost_impact": 2500
                    }
                },
                {
                    "name": "Additional Documentation",
                    "action_type": "submit_documents",
                    "parameters": {
                        "document_types": ["certificate_of_origin", "commercial_invoice"],
                        "estimated_time_savings": 12,
                        "cost_impact": 500
                    }
                }
            ]
        
        elif risk.risk_type == "quality_hold":
            scenarios = [
                {
                    "name": "Remote Inspection",
                    "action_type": "remote_inspection",
                    "parameters": {
                        "inspection_type": "video",
                        "estimated_time_savings": 18,
                        "cost_impact": 1500
                    }
                },
                {
                    "name": "Alternative Batch",
                    "action_type": "source_alternative",
                    "parameters": {
                        "source_location": "nearby_warehouse",
                        "estimated_time_savings": 24,
                        "cost_impact": 3000
                    }
                }
            ]
        
        return scenarios
    
    async def _run_simulation(self, scenario: Dict, risk: Risk, shipment: Shipment) -> Dict:
        """Run a single simulation scenario"""
        # Simulate computation time
        await asyncio.sleep(0.5)
        
        # Calculate scores
        time_score = min(1.0, scenario["parameters"].get("estimated_time_savings", 0) / 48)
        cost_score = max(0, 1 - (scenario["parameters"].get("cost_impact", 0) / 10000))
        risk_reduction = 0.7  # Assume 70% risk reduction
        
        overall_score = (time_score * 0.4 + cost_score * 0.3 + risk_reduction * 0.3)
        
        return {
            "scenario_name": scenario["name"],
            "action_type": scenario["action_type"],
            "parameters": scenario["parameters"],
            "time_savings_hours": scenario["parameters"].get("estimated_time_savings", 0),
            "cost_impact": scenario["parameters"].get("cost_impact", 0),
            "risk_reduction": risk_reduction,
            "confidence": overall_score,
            "feasibility": 0.8,
            "implementation_time_hours": 2
        }
    
    def _get_alternative_port(self, port_code: str) -> str:
        """Get alternative port for congestion mitigation"""
        alternatives = {
            "CNSHA": "CNNGB",  # Shanghai -> Ningbo
            "USLAX": "USLGB",  # Los Angeles -> Long Beach
            "NLRTM": "BEANR",  # Rotterdam -> Antwerp
            "SGSIN": "MYPKG",  # Singapore -> Port Klang
        }
        return alternatives.get(port_code, "ALT001")
    
    async def create_simulation(self, shipment_id: int, simulation_type: SimulationType,
                              parameters: Dict, session: AsyncSession) -> Simulation:
        """Create a new simulation record"""
        simulation = Simulation(
            shipment_id=shipment_id,
            simulation_type=simulation_type,
            parameters=parameters,
            status=SimulationStatus.PENDING,
            initiated_by="system"
        )
        
        session.add(simulation)
        await session.commit()
        await session.refresh(simulation)
        
        return simulation
    
    async def update_simulation_results(self, simulation_id: int, results: Dict,
                                      session: AsyncSession) -> Optional[Simulation]:
        """Update simulation results"""
        simulation = await session.get(Simulation, simulation_id)
        if simulation:
            simulation.status = SimulationStatus.COMPLETED
            simulation.results = results
            simulation.execution_time = (datetime.utcnow() - simulation.created_at).total_seconds()
            
            # Determine best option
            if results.get("simulations"):
                best_option = max(results["simulations"], key=lambda x: x.get("confidence", 0))
                simulation.best_option = best_option
                simulation.confidence_score = best_option.get("confidence", 0)
            
            await session.commit()
            await session.refresh(simulation)
        
        return simulation
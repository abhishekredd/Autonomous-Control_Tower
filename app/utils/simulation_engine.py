from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import numpy as np
from app.core.redis import redis_client
import json

class SimulationEngine:
    """Digital twin simulation engine for what-if analysis"""
    
    def __init__(self):
        self.scenario_cache = {}
        self.simulation_history = []
        
    async def simulate_mitigation_options(self, shipment_id: int,
                                        risk_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate various mitigation options for a risk"""
        risk_type = risk_data.get("type")
        severity = risk_data.get("severity", "medium")
        
        # Generate simulation scenarios
        scenarios = self._generate_mitigation_scenarios(risk_type, severity, shipment_id)
        
        # Run simulations
        simulation_results = []
        for scenario in scenarios:
            result = await self._run_simulation(scenario, shipment_id, risk_data)
            simulation_results.append(result)
        
        # Sort by overall score
        simulation_results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        # Cache results
        cache_key = f"simulation:{shipment_id}:{risk_type}"
        self.scenario_cache[cache_key] = {
            "results": simulation_results,
            "timestamp": datetime.utcnow().isoformat(),
            "risk_data": risk_data
        }
        
        # Store in Redis for real-time access
        await redis_client.setex(
            cache_key,
            3600,  # 1 hour
            json.dumps(simulation_results)
        )
        
        # Log simulation
        self.simulation_history.append({
            "shipment_id": shipment_id,
            "risk_type": risk_type,
            "scenarios_evaluated": len(scenarios),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return simulation_results
    
    def _generate_mitigation_scenarios(self, risk_type: str, severity: str,
                                     shipment_id: int) -> List[Dict[str, Any]]:
        """Generate mitigation scenarios based on risk type"""
        scenarios = []
        
        if risk_type == "port_congestion":
            scenarios = [
                {
                    "id": "port_alt_1",
                    "name": "Alternative Port Routing",
                    "type": "reroute",
                    "description": "Reroute to alternative port with less congestion",
                    "parameters": {
                        "action": "reroute",
                        "alternative_ports": ["CNNGB", "CNYTN", "DEHAM"],
                        "estimated_implementation_time": 4,  # hours
                        "complexity": "medium"
                    },
                    "cost_factors": ["port_fees", "additional_distance", "administrative"],
                    "time_factors": ["transit_time", "port_processing", "customs"]
                },
                {
                    "id": "schedule_adjust_1",
                    "name": "Schedule Optimization",
                    "type": "delay",
                    "description": "Adjust schedule to avoid peak congestion periods",
                    "parameters": {
                        "action": "delay",
                        "delay_hours": 12,
                        "optimization_type": "temporal",
                        "estimated_implementation_time": 2
                    },
                    "cost_factors": ["demurrage", "storage", "planning"],
                    "time_factors": ["wait_time", "rescheduling"]
                },
                {
                    "id": "mode_switch_1",
                    "name": "Inter-modal Transfer",
                    "type": "mode_switch",
                    "description": "Switch to alternative transport mode for affected segment",
                    "parameters": {
                        "action": "mode_switch",
                        "new_mode": "rail",
                        "switch_point": "nearest_intermodal_terminal",
                        "estimated_implementation_time": 8
                    },
                    "cost_factors": ["mode_switch_cost", "handling", "equipment"],
                    "time_factors": ["transfer_time", "coordination", "transit"]
                }
            ]
        
        elif risk_type == "customs_delay":
            scenarios = [
                {
                    "id": "expedite_1",
                    "name": "Expedited Clearance Service",
                    "type": "expedite",
                    "description": "Utilize premium customs clearance service",
                    "parameters": {
                        "action": "expedite_customs",
                        "service_level": "premium",
                        "estimated_implementation_time": 1
                    },
                    "cost_factors": ["service_fee", "expedite_charge", "documentation"],
                    "time_factors": ["clearance_time", "processing"]
                },
                {
                    "id": "documents_1",
                    "name": "Documentation Enhancement",
                    "type": "documentation",
                    "description": "Enhance and pre-submit documentation package",
                    "parameters": {
                        "action": "enhance_documents",
                        "document_types": ["certificate_of_origin", "commercial_invoice", "packing_list"],
                        "estimated_implementation_time": 6
                    },
                    "cost_factors": ["document_prep", "translation", "legal"],
                    "time_factors": ["preparation", "submission", "review"]
                }
            ]
        
        elif risk_type == "quality_hold":
            scenarios = [
                {
                    "id": "remote_inspect_1",
                    "name": "Remote Video Inspection",
                    "type": "remote_inspection",
                    "description": "Conduct remote inspection via video conference",
                    "parameters": {
                        "action": "remote_inspection",
                        "inspection_type": "video",
                        "estimated_implementation_time": 2
                    },
                    "cost_factors": ["technology", "personnel", "coordination"],
                    "time_factors": ["scheduling", "inspection", "reporting"]
                },
                {
                    "id": "alternative_source_1",
                    "name": "Alternative Source Activation",
                    "type": "alternative_source",
                    "description": "Activate alternative supply source for replacement",
                    "parameters": {
                        "action": "alternative_source",
                        "source_location": "nearest_warehouse",
                        "estimated_implementation_time": 12
                    },
                    "cost_factors": ["sourcing", "transport", "inventory"],
                    "time_factors": ["sourcing", "transport", "quality_check"]
                }
            ]
        
        return scenarios
    
    async def _run_simulation(self, scenario: Dict[str, Any], shipment_id: int,
                            risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single simulation scenario"""
        # Simulate computation time
        await asyncio.sleep(0.3)  # Simulate processing
        
        # Calculate various metrics
        cost_impact = await self._calculate_cost_impact(scenario, risk_data)
        time_impact = await self._calculate_time_impact(scenario, risk_data)
        risk_reduction = await self._calculate_risk_reduction(scenario, risk_data)
        feasibility = await self._assess_feasibility(scenario, shipment_id)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            cost_impact, time_impact, risk_reduction, feasibility
        )
        
        # Generate detailed analysis
        detailed_analysis = await self._generate_detailed_analysis(
            scenario, cost_impact, time_impact, risk_reduction
        )
        
        return {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "scenario_type": scenario["type"],
            "description": scenario["description"],
            "cost_impact": cost_impact,
            "time_impact": time_impact,
            "risk_reduction": risk_reduction,
            "feasibility_score": feasibility,
            "overall_score": overall_score,
            "implementation_time_hours": scenario["parameters"].get("estimated_implementation_time", 4),
            "detailed_analysis": detailed_analysis,
            "recommendation": self._generate_recommendation(overall_score, scenario),
            "simulation_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _calculate_cost_impact(self, scenario: Dict[str, Any],
                                   risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate cost impact of mitigation"""
        scenario_type = scenario["type"]
        base_cost = 10000  # Base shipment cost
        
        if scenario_type == "reroute":
            additional_cost = base_cost * 0.3  # 30% additional
            cost_breakdown = {
                "port_fees": additional_cost * 0.4,
                "additional_distance": additional_cost * 0.3,
                "administrative": additional_cost * 0.2,
                "miscellaneous": additional_cost * 0.1
            }
        
        elif scenario_type == "delay":
            delay_hours = scenario["parameters"].get("delay_hours", 12)
            additional_cost = (delay_hours / 24) * 500  # $500 per day demurrage
            cost_breakdown = {
                "demurrage": additional_cost * 0.6,
                "storage": additional_cost * 0.3,
                "planning": additional_cost * 0.1
            }
        
        elif scenario_type == "expedite":
            additional_cost = 2500  # Fixed expedite fee
            cost_breakdown = {
                "service_fee": additional_cost * 0.7,
                "expedite_charge": additional_cost * 0.2,
                "documentation": additional_cost * 0.1
            }
        
        else:
            additional_cost = base_cost * 0.15  # 15% default
            cost_breakdown = {"base": additional_cost}
        
        return {
            "additional_cost": additional_cost,
            "total_cost": base_cost + additional_cost,
            "cost_breakdown": cost_breakdown,
            "cost_efficiency": self._calculate_cost_efficiency(additional_cost, risk_data)
        }
    
    async def _calculate_time_impact(self, scenario: Dict[str, Any],
                                   risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate time impact of mitigation"""
        current_delay = risk_data.get("expected_delay_hours", 0)
        scenario_type = scenario["type"]
        
        if scenario_type == "reroute":
            time_savings = min(48, current_delay * 0.7)  # Up to 70% savings, max 48h
            implementation_time = scenario["parameters"].get("estimated_implementation_time", 4)
            net_savings = time_savings - implementation_time
        
        elif scenario_type == "delay":
            time_savings = -scenario["parameters"].get("delay_hours", 12)  # Negative (delay)
            implementation_time = 2
            net_savings = time_savings - implementation_time
        
        elif scenario_type == "expedite":
            time_savings = 20  # Fixed 20 hours savings
            implementation_time = 1
            net_savings = time_savings - implementation_time
        
        else:
            time_savings = 12  # Default
            implementation_time = 4
            net_savings = time_savings - implementation_time
        
        return {
            "time_savings_hours": max(-48, min(72, time_savings)),
            "implementation_time_hours": implementation_time,
            "net_time_impact_hours": net_savings,
            "schedule_impact": self._assess_schedule_impact(net_savings)
        }
    
    async def _calculate_risk_reduction(self, scenario: Dict[str, Any],
                                      risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk reduction from mitigation"""
        initial_severity = risk_data.get("severity", "medium")
        severity_scores = {"low": 0.3, "medium": 0.6, "high": 0.8, "critical": 0.95}
        initial_score = severity_scores.get(initial_severity, 0.6)
        
        scenario_type = scenario["type"]
        
        if scenario_type == "reroute":
            reduction = 0.7  # 70% risk reduction
        elif scenario_type == "expedite":
            reduction = 0.6  # 60% risk reduction
        elif scenario_type == "remote_inspection":
            reduction = 0.8  # 80% risk reduction
        else:
            reduction = 0.5  # 50% default
        
        new_score = initial_score * (1 - reduction)
        
        return {
            "risk_reduction_percent": reduction * 100,
            "initial_risk_score": initial_score,
            "new_risk_score": new_score,
            "residual_risk_level": self._score_to_level(new_score)
        }
    
    async def _assess_feasibility(self, scenario: Dict[str, Any],
                                shipment_id: int) -> float:
        """Assess feasibility of implementing the scenario"""
        # Factors affecting feasibility
        factors = {
            "implementation_time": 0.3,
            "resource_availability": 0.25,
            "regulatory_compliance": 0.2,
            "stakeholder_agreement": 0.15,
            "technical_complexity": 0.1
        }
        
        # Score each factor
        scores = {}
        
        # Implementation time factor (shorter is better)
        impl_time = scenario["parameters"].get("estimated_implementation_time", 4)
        scores["implementation_time"] = max(0, 1 - (impl_time / 24))
        
        # Resource availability (simulated)
        scores["resource_availability"] = 0.8
        
        # Regulatory compliance (simulated)
        scores["regulatory_compliance"] = 0.9 if scenario["type"] != "mode_switch" else 0.7
        
        # Stakeholder agreement (simulated)
        scores["stakeholder_agreement"] = 0.7
        
        # Technical complexity
        complexity = scenario["parameters"].get("complexity", "medium")
        complexity_scores = {"low": 0.9, "medium": 0.7, "high": 0.4}
        scores["technical_complexity"] = complexity_scores.get(complexity, 0.7)
        
        # Calculate weighted feasibility score
        feasibility = sum(score * factors[factor] for factor, score in scores.items())
        
        return min(1.0, max(0.0, feasibility))
    
    def _calculate_overall_score(self, cost_impact: Dict[str, Any],
                               time_impact: Dict[str, Any],
                               risk_reduction: Dict[str, Any],
                               feasibility: float) -> float:
        """Calculate overall scenario score"""
        # Weights
        weights = {
            "cost": 0.25,
            "time": 0.35,
            "risk": 0.30,
            "feasibility": 0.10
        }
        
        # Normalize scores
        cost_score = max(0, 1 - (cost_impact["additional_cost"] / 5000))
        time_score = max(0, 1 + (time_impact["net_time_impact_hours"] / 48))
        risk_score = risk_reduction["risk_reduction_percent"] / 100
        
        # Calculate weighted score
        overall = (
            cost_score * weights["cost"] +
            time_score * weights["time"] +
            risk_score * weights["risk"] +
            feasibility * weights["feasibility"]
        )
        
        return min(1.0, max(0.0, overall))
    
    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _generate_recommendation(self, overall_score: float,
                               scenario: Dict[str, Any]) -> str:
        """Generate recommendation based on score"""
        if overall_score >= 0.8:
            return "Highly recommended - Excellent balance of cost, time, and risk reduction"
        elif overall_score >= 0.6:
            return "Recommended - Good overall value with manageable trade-offs"
        elif overall_score >= 0.4:
            return "Consider with caution - Some benefits but significant trade-offs"
        else:
            return "Not recommended - Poor value proposition"
    
    async def simulate_route(self, route: Dict[str, Any],
                           constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a specific route"""
        # Route simulation logic
        await asyncio.sleep(0.2)  # Simulate processing
        
        return {
            "route_id": route.get("id"),
            "simulation_results": {
                "estimated_time_hours": route.get("estimated_time", 0),
                "estimated_cost": route.get("estimated_cost", 0),
                "risk_score": route.get("risk_score", 0.5),
                "reliability_score": 0.8,
                "carbon_impact": route.get("distance", 0) * 0.02  # kg CO2 per km
            },
            "constraints_met": self._check_constraints(route, constraints),
            "simulation_timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_what_if_analysis(self, base_scenario: Dict[str, Any],
                                 variations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run what-if analysis with multiple variations"""
        results = []
        
        for variation in variations:
            # Combine base scenario with variation
            scenario = {**base_scenario, **variation}
            
            # Run simulation
            result = await self._run_what_if_simulation(scenario)
            results.append({
                "variation": variation,
                "result": result,
                "comparison": self._compare_to_base(base_scenario, result)
            })
        
        return {
            "base_scenario": base_scenario,
            "variations": results,
            "best_variation": max(results, key=lambda x: x["result"].get("score", 0)),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

# Global instance
simulation_engine = SimulationEngine()
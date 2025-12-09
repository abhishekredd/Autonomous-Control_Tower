from typing import Dict, Any, List
from datetime import datetime
from app.mcp.agents.base import BaseAgent
from app.utils.geocoding import calculate_route, find_alternative_routes
from app.utils.simulation_engine import SimulationEngine
import json

class RouteOptimizerAgent(BaseAgent):
    """MCP Agent for route optimization and re-routing"""
    
    def __init__(self, agent_id: str = "route_optimizer_01"):
        super().__init__(agent_id, "route_optimizer")
        self.simulation_engine = SimulationEngine()
        self.route_cache = {}
        
    def _get_agent_channels(self) -> List[str]:
        """Get agent-specific Redis channels"""
        return [
            "risk:detected",
            "shipment:reroute:requested",
            "port:congestion:updates",
            "weather:alerts",
            "route:optimization:requested"
        ]
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages"""
        message_type = message.get("message_type")
        
        if message_type == "optimize_route":
            return await self._handle_optimize_route(message)
        elif message_type == "find_alternatives":
            return await self._handle_find_alternatives(message)
        elif message_type == "calculate_reroute_impact":
            return await self._handle_calculate_reroute_impact(message)
        elif message_type == "emergency_reroute":
            return await self._handle_emergency_reroute(message)
        else:
            return {"error": f"Unknown message type: {message_type}"}
    
    async def _handle_optimize_route(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route optimization request"""
        content = message.get("content", {})
        shipment_id = content.get("shipment_id")
        current_route = content.get("current_route", {})
        constraints = content.get("constraints", {})
        
        # Generate alternative routes
        alternatives = await self._generate_alternative_routes(
            current_route, constraints
        )
        
        # Evaluate each alternative
        evaluated_routes = []
        for route in alternatives:
            evaluation = await self._evaluate_route(route, constraints)
            evaluated_routes.append({
                "route": route,
                "evaluation": evaluation,
                "overall_score": evaluation.get("overall_score", 0)
            })
        
        # Sort by score
        evaluated_routes.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Get best route
        best_route = evaluated_routes[0] if evaluated_routes else None
        
        # Log activity
        await self.log_activity(
            "route_optimization",
            {
                "shipment_id": shipment_id,
                "alternatives_generated": len(alternatives),
                "best_route_score": best_route["overall_score"] if best_route else 0,
                "constraints": constraints
            }
        )
        
        return {
            "shipment_id": shipment_id,
            "alternatives": [
                {
                    "route_id": route["route"].get("id"),
                    "description": route["route"].get("description"),
                    "overall_score": route["overall_score"],
                    "time_estimate": route["evaluation"].get("time_estimate"),
                    "cost_estimate": route["evaluation"].get("cost_estimate"),
                    "risk_score": route["evaluation"].get("risk_score")
                }
                for route in evaluated_routes[:5]  # Return top 5
            ],
            "recommendation": best_route["route"] if best_route else None,
            "optimization_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_emergency_reroute(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency reroute request"""
        content = message.get("content", {})
        shipment_id = content.get("shipment_id")
        risk_data = content.get("risk_data", {})
        urgency = content.get("urgency", "high")
        
        # Get current location and destination
        current_location = risk_data.get("current_location")
        destination = risk_data.get("destination")
        
        if not current_location or not destination:
            return {"error": "Missing location information"}
        
        # Find emergency alternatives
        emergency_routes = await self._find_emergency_routes(
            current_location, destination, urgency
        )
        
        # Simulate each emergency route
        simulations = []
        for route in emergency_routes:
            simulation = await self.simulation_engine.simulate_route(
                route=route,
                constraints={"urgency": urgency, "risk_tolerance": "low"}
            )
            simulations.append({
                "route": route,
                "simulation": simulation,
                "time_savings": simulation.get("time_savings", 0),
                "risk_reduction": simulation.get("risk_reduction", 0)
            })
        
        # Select best emergency route
        if simulations:
            best_route = max(simulations, key=lambda x: x["time_savings"])
            
            # Prepare reroute action
            reroute_action = {
                "action_type": "emergency_reroute",
                "shipment_id": shipment_id,
                "new_route": best_route["route"],
                "expected_time_savings": best_route["time_savings"],
                "risk_reduction": best_route["risk_reduction"],
                "implementation_time": "immediate",
                "urgency": urgency
            }
            
            # Send to action executor
            await self.send_message(
                recipient_agent="action_executor_01",
                message_type="execute_reroute",
                content=reroute_action
            )
            
            return {
                "shipment_id": shipment_id,
                "emergency_reroute_initiated": True,
                "selected_route": best_route["route"].get("id"),
                "expected_time_savings": best_route["time_savings"],
                "action_sent_to": "action_executor_01"
            }
        
        return {"error": "No emergency routes available"}
    
    async def _generate_alternative_routes(self, current_route: Dict[str, Any],
                                         constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative routes"""
        origin = current_route.get("origin")
        destination = current_route.get("destination")
        current_location = current_route.get("current_location", origin)
        
        if not origin or not destination:
            return []
        
        # Generate route alternatives based on constraints
        alternatives = []
        
        # Alternative 1: Different ports
        if constraints.get("allow_port_change", True):
            alt1 = await self._generate_port_alternative(
                current_route, constraints
            )
            if alt1:
                alternatives.append(alt1)
        
        # Alternative 2: Mode switching
        if constraints.get("allow_mode_switch", False):
            alt2 = await self._generate_mode_switch_alternative(
                current_route, constraints
            )
            if alt2:
                alternatives.append(alt2)
        
        # Alternative 3: Multi-modal
        if constraints.get("allow_multimodal", True):
            alt3 = await self._generate_multimodal_alternative(
                current_route, constraints
            )
            if alt3:
                alternatives.append(alt3)
        
        # Alternative 4: Speed optimization
        alt4 = await self._generate_speed_optimized_alternative(
            current_route, constraints
        )
        if alt4:
            alternatives.append(alt4)
        
        return alternatives
    
    async def _evaluate_route(self, route: Dict[str, Any],
                            constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a route against constraints"""
        # Calculate time estimate
        time_estimate = await self._calculate_route_time(route)
        
        # Calculate cost estimate
        cost_estimate = await self._calculate_route_cost(route)
        
        # Calculate risk score
        risk_score = await self._calculate_route_risk(route)
        
        # Check constraints
        constraints_met = self._check_constraints(
            route, time_estimate, cost_estimate, risk_score, constraints
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            time_estimate, cost_estimate, risk_score, constraints
        )
        
        return {
            "time_estimate": time_estimate,
            "cost_estimate": cost_estimate,
            "risk_score": risk_score,
            "constraints_met": constraints_met,
            "overall_score": overall_score,
            "feasibility": self._assess_feasibility(route)
        }
    
    def _calculate_overall_score(self, time_estimate: float, cost_estimate: float,
                               risk_score: float, constraints: Dict[str, Any]) -> float:
        """Calculate overall route score"""
        # Weight factors from constraints
        time_weight = constraints.get("time_weight", 0.4)
        cost_weight = constraints.get("cost_weight", 0.3)
        risk_weight = constraints.get("risk_weight", 0.3)
        
        # Normalize scores (lower is better for time and cost)
        max_time = constraints.get("max_time", 240)  # hours
        max_cost = constraints.get("max_cost", 50000)
        
        time_score = max(0, 1 - (time_estimate / max_time))
        cost_score = max(0, 1 - (cost_estimate / max_cost))
        risk_score_normalized = max(0, 1 - risk_score)
        
        return (
            time_score * time_weight +
            cost_score * cost_weight +
            risk_score_normalized * risk_weight
        )
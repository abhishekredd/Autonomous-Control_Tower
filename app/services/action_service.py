from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.shipment import Shipment, ShipmentStatus, ShipmentRoute
from app.models.risk import Risk, RiskStatus
from app.core.redis import redis_client
import json

class ActionService:
    """Service for executing autonomous actions"""
    
    async def execute_action(self, shipment_id: int, action_type: str,
                           parameters: Dict) -> Dict:
        """Execute an autonomous action"""
        print(f"⚡ Executing action: {action_type} for shipment {shipment_id}")
        
        try:
            if action_type == "reroute":
                return await self._execute_reroute(shipment_id, parameters)
            elif action_type == "mode_switch":
                return await self._execute_mode_switch(shipment_id, parameters)
            elif action_type == "expedite_customs":
                return await self._execute_expedite_customs(shipment_id, parameters)
            elif action_type == "delay":
                return await self._execute_schedule_adjustment(shipment_id, parameters)
            else:
                return await self._execute_generic_action(shipment_id, action_type, parameters)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_type": action_type,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_reroute(self, shipment_id: int, parameters: Dict) -> Dict:
        """Execute shipment rerouting"""
        async with AsyncSessionLocal() as session:
            shipment = await session.get(Shipment, shipment_id)
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            # Create new route
            new_route = ShipmentRoute(
                shipment_id=shipment_id,
                route_type="alternative",
                waypoints=parameters.get("waypoints", []),
                total_distance=parameters.get("total_distance", 0),
                estimated_duration=parameters.get("estimated_duration", 0),
                cost_estimate=parameters.get("cost_estimate", 0),
                risk_score=parameters.get("risk_score", 0.5),
                is_active=True
            )
            
            # Deactivate previous routes
            await session.execute(
                "UPDATE shipment_routes SET is_active = false WHERE shipment_id = :shipment_id",
                {"shipment_id": shipment_id}
            )
            
            session.add(new_route)
            
            # Update shipment
            if parameters.get("alternative_port"):
                shipment.next_port = parameters["alternative_port"]
            
            shipment.metadata = {
                **shipment.metadata,
                "rerouted_at": datetime.utcnow().isoformat(),
                "reroute_reason": "port_congestion",
                "new_route_id": new_route.id
            }
            
            await session.commit()
            
            # Publish event
            await redis_client.publish(
                "action_executed",
                json.dumps({
                    "shipment_id": shipment_id,
                    "action_type": "reroute",
                    "new_port": parameters.get("alternative_port"),
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "success": True,
                "action_type": "reroute",
                "new_port": parameters.get("alternative_port"),
                "route_id": new_route.id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_mode_switch(self, shipment_id: int, parameters: Dict) -> Dict:
        """Execute transport mode switch"""
        async with AsyncSessionLocal() as session:
            shipment = await session.get(Shipment, shipment_id)
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            old_mode = shipment.mode
            new_mode = parameters.get("new_mode")
            
            if not new_mode:
                return {"success": False, "error": "No new mode specified"}
            
            shipment.mode = new_mode
            shipment.metadata = {
                **shipment.metadata,
                "mode_switched_at": datetime.utcnow().isoformat(),
                "previous_mode": old_mode,
                "mode_switch_reason": parameters.get("reason", "optimization")
            }
            
            await session.commit()
            
            # Publish event
            await redis_client.publish(
                "action_executed",
                json.dumps({
                    "shipment_id": shipment_id,
                    "action_type": "mode_switch",
                    "old_mode": old_mode,
                    "new_mode": new_mode,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "success": True,
                "action_type": "mode_switch",
                "old_mode": old_mode,
                "new_mode": new_mode,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_expedite_customs(self, shipment_id: int, parameters: Dict) -> Dict:
        """Execute expedited customs clearance"""
        async with AsyncSessionLocal() as session:
            shipment = await session.get(Shipment, shipment_id)
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            service_level = parameters.get("service_level", "premium")
            
            shipment.metadata = {
                **shipment.metadata,
                "customs_expedited_at": datetime.utcnow().isoformat(),
                "customs_service_level": service_level,
                "customs_estimated_clearance": (datetime.utcnow() + timedelta(hours=4)).isoformat()
            }
            
            await session.commit()
            
            # Publish event
            await redis_client.publish(
                "action_executed",
                json.dumps({
                    "shipment_id": shipment_id,
                    "action_type": "expedite_customs",
                    "service_level": service_level,
                    "estimated_clearance": "4 hours",
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "success": True,
                "action_type": "expedite_customs",
                "service_level": service_level,
                "estimated_clearance_hours": 4,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_schedule_adjustment(self, shipment_id: int, parameters: Dict) -> Dict:
        """Execute schedule adjustment/delay"""
        async with AsyncSessionLocal() as session:
            shipment = await session.get(Shipment, shipment_id)
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            delay_hours = parameters.get("delay_hours", 12)
            new_eta = shipment.estimated_arrival + timedelta(hours=delay_hours)
            
            shipment.estimated_arrival = new_eta
            shipment.metadata = {
                **shipment.metadata,
                "schedule_adjusted_at": datetime.utcnow().isoformat(),
                "adjustment_reason": parameters.get("reason", "port_congestion"),
                "delay_hours": delay_hours
            }
            
            await session.commit()
            
            # Publish event
            await redis_client.publish(
                "action_executed",
                json.dumps({
                    "shipment_id": shipment_id,
                    "action_type": "schedule_adjustment",
                    "delay_hours": delay_hours,
                    "new_eta": new_eta.isoformat(),
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            return {
                "success": True,
                "action_type": "schedule_adjustment",
                "delay_hours": delay_hours,
                "new_eta": new_eta.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
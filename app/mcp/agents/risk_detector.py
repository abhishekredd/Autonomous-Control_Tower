from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.mcp.agents.base import BaseAgent
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService
import json

class RiskDetectorAgent(BaseAgent):
    """MCP Agent for detecting supply chain risks"""
    
    def __init__(self, agent_id: str = "risk_detector_01"):
        super().__init__(agent_id, "risk_detector")
        self.risk_service = RiskService()
        self.shipment_service = ShipmentService()
        self.risk_patterns = self._load_risk_patterns()
        
    def _get_agent_channels(self) -> List[str]:
        """Get agent-specific Redis channels"""
        return [
            "shipment:updates",
            "shipment:created",
            "shipment:status_changed",
            "risk:check:requested",
            "weather:updates",
            "port:congestion:updates"
        ]
    
    def _load_risk_patterns(self) -> Dict[str, Any]:
        """Load risk detection patterns"""
        return {
            "port_congestion": {
                "threshold": 0.7,
                "check_interval": 300,  # 5 minutes
                "data_sources": ["port_api", "ais_data", "schedule_data"]
            },
            "customs_delay": {
                "threshold": 0.6,
                "check_interval": 600,  # 10 minutes
                "data_sources": ["customs_api", "document_status"]
            },
            "quality_hold": {
                "threshold": 0.8,
                "check_interval": 900,  # 15 minutes
                "data_sources": ["inspection_reports", "quality_api"]
            },
            "weather_impact": {
                "threshold": 0.5,
                "check_interval": 300,
                "data_sources": ["weather_api", "storm_tracking"]
            }
        }
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages"""
        message_type = message.get("message_type")
        
        if message_type == "detect_risks":
            return await self._handle_detect_risks(message)
        elif message_type == "analyze_shipment":
            return await self._handle_analyze_shipment(message)
        elif message_type == "check_specific_risk":
            return await self._handle_check_specific_risk(message)
        else:
            return {"error": f"Unknown message type: {message_type}"}
    
    async def _handle_detect_risks(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle risk detection request"""
        shipment_id = message.get("content", {}).get("shipment_id")
        
        if not shipment_id:
            return {"error": "No shipment_id provided"}
        
        async with self.get_database_session() as session:
            # Get shipment
            shipment = await self.shipment_service.get_shipment(shipment_id, session)
            
            if not shipment:
                return {"error": f"Shipment {shipment_id} not found"}
            
            # Detect risks
            risks = await self.risk_service.detect_risks(shipment_id, session)
            
            # Log activity
            await self.log_activity(
                "risk_detection",
                {
                    "shipment_id": shipment_id,
                    "risks_detected": len(risks),
                    "risk_types": [risk.risk_type for risk in risks]
                }
            )
            
            # Send notifications for critical risks
            for risk in risks:
                if risk.severity in ["high", "critical"]:
                    await self._notify_critical_risk(risk, shipment)
            
            return {
                "shipment_id": shipment_id,
                "risks_detected": len(risks),
                "risks": [
                    {
                        "id": risk.id,
                        "type": risk.risk_type,
                        "severity": risk.severity,
                        "description": risk.description,
                        "confidence": risk.confidence
                    }
                    for risk in risks
                ]
            }
    
    async def _handle_analyze_shipment(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive shipment risk analysis"""
        shipment_id = message.get("content", {}).get("shipment_id")
        
        async with self.get_database_session() as session:
            shipment = await self.shipment_service.get_shipment_with_relations(shipment_id, session)
            
            if not shipment:
                return {"error": f"Shipment {shipment_id} not found"}
            
            # Analyze different risk factors
            risk_analysis = await self._analyze_risk_factors(shipment)
            
            # Calculate overall risk score
            overall_score = self._calculate_overall_risk_score(risk_analysis)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_analysis)
            
            return {
                "shipment_id": shipment_id,
                "overall_risk_score": overall_score,
                "risk_level": self._get_risk_level(overall_score),
                "risk_analysis": risk_analysis,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    async def _analyze_risk_factors(self, shipment) -> Dict[str, Any]:
        """Analyze different risk factors for a shipment"""
        analysis = {}
        
        # Port congestion risk
        if shipment.next_port:
            analysis["port_congestion"] = await self._analyze_port_congestion(shipment.next_port)
        
        # Customs risk
        analysis["customs"] = await self._analyze_customs_risk(shipment)
        
        # Quality risk
        analysis["quality"] = await self._analyze_quality_risk(shipment)
        
        # Weather risk
        if shipment.current_location:
            analysis["weather"] = await self._analyze_weather_risk(shipment.current_location)
        
        # Schedule risk
        analysis["schedule"] = self._analyze_schedule_risk(shipment)
        
        return analysis
    
    async def _analyze_port_congestion(self, port_code: str) -> Dict[str, Any]:
        """Analyze port congestion risk"""
        # Simulate port congestion analysis
        congestion_data = {
            "CNSHA": {"level": 0.8, "wait_time": 48, "alternatives": ["CNNGB", "CNYTN"]},
            "NLRTM": {"level": 0.6, "wait_time": 24, "alternatives": ["BEANR", "DEHAM"]},
            "USLAX": {"level": 0.7, "wait_time": 36, "alternatives": ["USLGB", "USOAK"]}
        }
        
        data = congestion_data.get(port_code, {"level": 0.3, "wait_time": 6, "alternatives": []})
        
        return {
            "port": port_code,
            "congestion_level": data["level"],
            "risk_score": data["level"],
            "estimated_wait_hours": data["wait_time"],
            "alternative_ports": data["alternatives"],
            "recommendation": "Consider alternative port" if data["level"] > 0.7 else "Monitor situation"
        }
    
    def _calculate_overall_risk_score(self, risk_analysis: Dict[str, Any]) -> float:
        """Calculate overall risk score from analysis"""
        if not risk_analysis:
            return 0.0
        
        scores = []
        weights = {
            "port_congestion": 0.3,
            "customs": 0.25,
            "quality": 0.2,
            "weather": 0.15,
            "schedule": 0.1
        }
        
        for risk_type, analysis in risk_analysis.items():
            if "risk_score" in analysis:
                weight = weights.get(risk_type, 0.1)
                scores.append(analysis["risk_score"] * weight)
        
        return min(1.0, sum(scores)) if scores else 0.0
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
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
    
    def _generate_recommendations(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on risk analysis"""
        recommendations = []
        
        for risk_type, analysis in risk_analysis.items():
            if analysis.get("risk_score", 0) > 0.6:
                if "recommendation" in analysis:
                    recommendations.append(analysis["recommendation"])
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    async def _notify_critical_risk(self, risk, shipment):
        """Notify about critical risk"""
        notification = {
            "type": "critical_risk",
            "shipment_id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "risk_id": risk.id,
            "risk_type": risk.risk_type,
            "severity": risk.severity,
            "description": risk.description,
            "confidence": risk.confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to orchestrator
        await self.send_message(
            recipient_agent="orchestrator_01",
            message_type="critical_risk_detected",
            content=notification
        )
        
        # Broadcast to dashboard
        await self.broadcast_message(
            message_type="dashboard_alert",
            content=notification
        )
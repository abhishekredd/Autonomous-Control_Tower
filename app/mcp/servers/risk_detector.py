"""
MCP Risk Detector Server
"""
import asyncio
from datetime import datetime
from typing import Dict, List
import json
from app.mcp import MCPServer, MCPMessage, MCPAgentType
from app.core.redis import redis_client
from app.services.risk_service import RiskService
from app.core.database import AsyncSessionLocal

class RiskDetectorServer(MCPServer):
    """MCP server for risk detection"""
    
    def __init__(self):
        super().__init__(MCPAgentType.RISK_DETECTOR)
        self.risk_service = RiskService()
        
    async def start(self):
        await super().start()
        
        # Subscribe to shipment updates
        await redis_client.subscribe("shipment_updates")
        
        # Start message processing loop
        asyncio.create_task(self._message_loop())
    
    async def _message_loop(self):
        """Main message processing loop"""
        while self.is_running:
            try:
                # Check for new messages
                message = await redis_client.get_message()
                if message:
                    await self._process_redis_message(message)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Risk detector error: {e}")
                await asyncio.sleep(5)
    
    async def _process_redis_message(self, message: Dict):
        """Process Redis message"""
        channel = message.get("channel")
        data = message.get("data")
        
        if channel == "shipment_updates" and data:
            shipment_data = json.loads(data)
            await self._analyze_shipment_risks(shipment_data)
    
    async def _analyze_shipment_risks(self, shipment_data: Dict):
        """Analyze risks for a shipment"""
        shipment_id = shipment_data.get("id")
        
        if not shipment_id:
            return
        
        async with AsyncSessionLocal() as session:
            risks = await self.risk_service.detect_risks(shipment_id, session)
            
            if risks:
                # Save risks to database
                for risk in risks:
                    session.add(risk)
                await session.commit()
                
                # Send MCP message about detected risks
                for risk in risks:
                    mcp_message = MCPMessage(
                        message_id=f"risk_{risk.id}",
                        sender=self.agent_type,
                        receiver=MCPAgentType.ROUTE_OPTIMIZER,
                        message_type="risk_detected",
                        content={
                            "shipment_id": shipment_id,
                            "risk_id": risk.id,
                            "risk_type": risk.risk_type,
                            "severity": risk.severity,
                            "description": risk.description,
                            "confidence": risk.confidence
                        },
                        timestamp=datetime.utcnow(),
                        context_id=f"shipment_{shipment_id}"
                    )
                    
                    await self.send_message(mcp_message)
    
    async def process_message(self, message: MCPMessage) -> MCPMessage:
        """Process incoming MCP message"""
        if message.message_type == "analyze_risks":
            return await self._handle_analyze_risks(message)
        elif message.message_type == "get_risk_history":
            return await self._handle_get_risk_history(message)
        else:
            return MCPMessage(
                message_id=f"error_{message.message_id}",
                sender=self.agent_type,
                receiver=message.sender,
                message_type="error",
                content={"error": "Unknown message type"},
                timestamp=datetime.utcnow()
            )
    
    async def _handle_analyze_risks(self, message: MCPMessage) -> MCPMessage:
        """Handle risk analysis request"""
        shipment_id = message.content.get("shipment_id")
        
        async with AsyncSessionLocal() as session:
            risks = await self.risk_service.detect_risks(shipment_id, session)
            
            return MCPMessage(
                message_id=f"response_{message.message_id}",
                sender=self.agent_type,
                receiver=message.sender,
                message_type="risk_analysis_complete",
                content={
                    "shipment_id": shipment_id,
                    "risks_detected": len(risks),
                    "risks": [
                        {
                            "type": risk.risk_type,
                            "severity": risk.severity,
                            "description": risk.description
                        }
                        for risk in risks
                    ]
                },
                timestamp=datetime.utcnow(),
                context_id=message.context_id
            )

async def main():
    """Main entry point for MCP Risk Detector Server"""
    server = RiskDetectorServer()
    await server.start()
    
    # Keep server running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
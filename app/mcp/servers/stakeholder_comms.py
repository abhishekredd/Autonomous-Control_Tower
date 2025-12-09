"""
MCP Stakeholder Communications Server
"""
import asyncio
from datetime import datetime
from typing import Dict, List
from app.mcp import MCPServer, MCPMessage, MCPAgentType
from app.services.communication_service import CommunicationService
from openai import AsyncOpenAI
from app.core.config import settings

class StakeholderCommsServer(MCPServer):
    """MCP server for stakeholder communications"""
    
    def __init__(self):
        super().__init__(MCPAgentType.STAKEHOLDER_COMMS)
        self.communication_service = CommunicationService()
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
    async def start(self):
        await super().start()
        print("💬 Stakeholder Comms MCP Server started")
    
    async def process_message(self, message: MCPMessage) -> MCPMessage:
        """Process incoming MCP message"""
        if message.message_type == "route_optimized":
            return await self._handle_route_optimized(message)
        elif message.message_type == "action_executed":
            return await self._handle_action_executed(message)
        elif message.message_type == "notify_stakeholders":
            return await self._handle_notify_stakeholders(message)
        else:
            return MCPMessage(
                message_id=f"error_{message.message_id}",
                sender=self.agent_type,
                receiver=message.sender,
                message_type="error",
                content={"error": "Unknown message type"},
                timestamp=datetime.utcnow()
            )
    
    async def _handle_route_optimized(self, message: MCPMessage) -> MCPMessage:
        """Handle route optimized message"""
        shipment_id = message.content.get("shipment_id")
        recommended_action = message.content.get("recommended_action")
        
        if recommended_action:
            # Generate notification message using AI
            notification_message = await self._generate_ai_notification(
                shipment_id=shipment_id,
                action_type=recommended_action.get("action_type"),
                action_details=recommended_action
            )
            
            # Notify stakeholders
            await self.communication_service.notify_stakeholders(
                shipment_id=shipment_id,
                risk_id=message.content.get("risk_id"),
                action_taken=recommended_action.get("action_type"),
                action_result={"message": notification_message}
            )
        
        return MCPMessage(
            message_id=f"response_{message.message_id}",
            sender=self.agent_type,
            receiver=message.sender,
            message_type="notifications_sent",
            content={
                "shipment_id": shipment_id,
                "notifications_sent": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow(),
            context_id=message.context_id
        )
    
    async def _generate_ai_notification(self, shipment_id: int,
                                      action_type: str,
                                      action_details: Dict) -> str:
        """Generate AI-powered notification message"""
        try:
            if not settings.OPENAI_API_KEY:
                return self._generate_fallback_message(action_type, action_details)
            
            prompt = f"""
            Generate a professional notification message about an autonomous action taken on a shipment.
            
            Shipment ID: {shipment_id}
            Action Type: {action_type}
            Action Details: {action_details}
            
            The message should:
            1. Clearly state what action was taken
            2. Explain why it was necessary
            3. Describe the expected benefits
            4. Provide any necessary follow-up instructions
            5. Be professional but friendly
            
            Format the message for email communication.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a supply chain communication specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"AI notification generation failed: {e}")
            return self._generate_fallback_message(action_type, action_details)
    
    def _generate_fallback_message(self, action_type: str, action_details: Dict) -> str:
        """Generate fallback notification message"""
        templates = {
            "reroute": """
            An autonomous decision has been made to reroute your shipment to avoid delays.
            The shipment will now take an alternative route which is expected to save {time_savings} hours.
            New estimated arrival: {new_eta}.
            """,
            "mode_switch": """
            The transportation mode for your shipment has been changed from {old_mode} to {new_mode}.
            This change is expected to improve delivery time by {time_savings} hours.
            """,
            "expedite_customs": """
            Expedited customs clearance has been requested for your shipment.
            This service should reduce clearance time to approximately {clearance_time} hours.
            """
        }
        
        return templates.get(action_type, "An autonomous action has been taken to optimize your shipment.")

async def main():
    """Main entry point for MCP Stakeholder Comms Server"""
    server = StakeholderCommsServer()
    await server.start()
    
    # Keep server running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
from typing import List, Dict
import asyncio
from datetime import datetime
from app.core.redis import redis_client
import json

class CommunicationService:
    """Service for coordinating stakeholder communication"""
    
    async def notify_stakeholders(self, shipment_id: int, risk_id: int,
                                action_taken: str, action_result: Dict):
        """Notify all stakeholders about an action taken"""
        # Get stakeholder contacts (simplified)
        stakeholders = await self._get_shipment_stakeholders(shipment_id)
        
        # Generate notification messages
        messages = self._generate_notification_messages(
            shipment_id, risk_id, action_taken, action_result, stakeholders
        )
        
        # Send notifications
        tasks = []
        for message in messages:
            tasks.append(self._send_notification(message))
        
        # Run in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        
        return {
            "successful": successful,
            "total": len(results),
            "stakeholders_notified": len(stakeholders)
        }
    
    async def notify_operations_team(self, message: str, data: Dict = None):
        """Notify operations team"""
        notification = {
            "type": "operations_alert",
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "urgency": "high"
        }
        
        await redis_client.publish(
            "operations_notifications",
            json.dumps(notification)
        )
        
        # Also send to Slack/Email in production
        print(f"📢 Operations Alert: {message}")
        
        return {"success": True}
    
    async def _get_shipment_stakeholders(self, shipment_id: int) -> List[Dict]:
        """Get stakeholders for a shipment (simplified)"""
        # In production, this would query the database
        return [
            {
                "type": "shipper",
                "name": "Acme Corp",
                "email": "shipping@acmecorp.com",
                "notification_preferences": ["email", "dashboard"]
            },
            {
                "type": "consignee",
                "name": "Global Imports",
                "email": "receiving@globalimports.com",
                "notification_preferences": ["email", "sms"]
            },
            {
                "type": "carrier",
                "name": "Ocean Shipping Co",
                "email": "operations@oceanshipping.com",
                "notification_preferences": ["api", "email"]
            },
            {
                "type": "customs_broker",
                "name": "Quick Clear Customs",
                "email": "notifications@quickclear.com",
                "notification_preferences": ["email", "portal"]
            }
        ]
    
    def _generate_notification_messages(self, shipment_id: int, risk_id: int,
                                      action_taken: str, action_result: Dict,
                                      stakeholders: List[Dict]) -> List[Dict]:
        """Generate notification messages for stakeholders"""
        messages = []
        
        base_message = self._get_base_message(action_taken, action_result)
        
        for stakeholder in stakeholders:
            message = {
                "stakeholder": stakeholder,
                "shipment_id": shipment_id,
                "risk_id": risk_id,
                "action_taken": action_taken,
                "message": self._personalize_message(base_message, stakeholder),
                "channels": stakeholder["notification_preferences"],
                "timestamp": datetime.utcnow().isoformat()
            }
            messages.append(message)
        
        return messages
    
    def _get_base_message(self, action_taken: str, action_result: Dict) -> str:
        """Get base notification message for action"""
        messages = {
            "reroute": """
🚢 ACTION TAKEN: Shipment Rerouted

An autonomous decision has been made to reroute your shipment to avoid delays.

Action: Emergency reroute through alternative corridor
Reason: Port congestion detected
Expected Time Savings: {time_savings} hours
New ETA: {new_eta}

You can track the updated route in your dashboard.
            """,
            "mode_switch": """
🔄 ACTION TAKEN: Transport Mode Changed

The transportation mode for your shipment has been changed to ensure timely delivery.

Action: Mode switched from {old_mode} to {new_mode}
Reason: Optimization for faster delivery
Impact: {time_savings} hours saved

The shipment is now en route via the new mode.
            """,
            "expedite_customs": """
⚡ ACTION TAKEN: Customs Clearance Expedited

Expedited customs clearance has been requested for your shipment.

Action: Premium customs clearance service
Service Level: {service_level}
Expected Clearance: Within {clearance_time} hours
Reference: {reference_number}

This service ensures faster clearance at the port.
            """
        }
        
        return messages.get(action_taken, "An autonomous action has been taken on your shipment.")
    
    def _personalize_message(self, base_message: str, stakeholder: Dict) -> str:
        """Personalize message for stakeholder"""
        # Add stakeholder-specific information
        personalized = f"Dear {stakeholder['name']},\n\n{base_message}\n\n"
        personalized += "Best regards,\nAutonomous Control Tower Team"
        return personalized
    
    async def _send_notification(self, message: Dict) -> bool:
        """Send a notification via appropriate channels"""
        try:
            # Simulate sending notifications
            for channel in message["channels"]:
                if channel == "email":
                    await self._send_email(message)
                elif channel == "sms":
                    await self._send_sms(message)
                elif channel == "api":
                    await self._send_api_notification(message)
            
            return True
        except Exception as e:
            print(f"Notification error: {e}")
            return False
    
    async def _send_email(self, message: Dict):
        """Send email notification"""
        # In production, integrate with SendGrid/Mailgun
        print(f"📧 Email sent to {message['stakeholder']['email']}: {message['message'][:100]}...")
        await asyncio.sleep(0.1)
    
    async def _send_sms(self, message: Dict):
        """Send SMS notification"""
        # In production, integrate with Twilio
        print(f"📱 SMS sent to {message['stakeholder'].get('phone', 'N/A')}")
        await asyncio.sleep(0.1)
    
    async def _send_api_notification(self, message: Dict):
        """Send API notification"""
        # In production, call stakeholder's API
        print(f"🔌 API notification sent to {message['stakeholder']['name']}")
        await asyncio.sleep(0.1)
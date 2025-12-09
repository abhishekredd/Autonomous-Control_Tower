from typing import Dict, Any, List
from datetime import datetime
from app.mcp.agents.base import BaseAgent
from openai import AsyncOpenAI
from app.core.config import settings
import json

class StakeholderCommsAgent(BaseAgent):
    """MCP Agent for stakeholder communication"""
    
    def __init__(self, agent_id: str = "stakeholder_comms_01"):
        super().__init__(agent_id, "stakeholder_comms")
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.templates = self._load_templates()
        self.stakeholder_profiles = self._load_stakeholder_profiles()
        
    def _load_templates(self) -> Dict[str, Any]:
        """Load communication templates"""
        return {
            "delay_notification": {
                "email": {
                    "subject": "Update on Your Shipment {tracking_number}",
                    "body": """
Dear {stakeholder_name},

We're writing to inform you that shipment {tracking_number} is experiencing a delay.

Current Status: {current_status}
Estimated Delay: {delay_hours} hours
Reason: {delay_reason}
New Estimated Arrival: {new_eta}

Our autonomous control tower is analyzing alternative options to minimize impact.

You can track the updated status here: {tracking_url}

Best regards,
Autonomous Control Tower Team
                    """
                },
                "sms": "Shipment {tracking_number} delayed by {delay_hours}h. New ETA: {new_eta}. Details: {tracking_url}"
            },
            "reroute_notification": {
                "email": {
                    "subject": "Action Taken: Shipment {tracking_number} Rerouted",
                    "body": """
Dear {stakeholder_name},

An autonomous decision has been made to reroute shipment {tracking_number}.

Action: Emergency reroute through alternative corridor
Reason: {reroute_reason}
Expected Time Savings: {time_savings} hours
New Route: {new_route}
New Estimated Arrival: {new_eta}

This action was taken to ensure timely delivery despite unforeseen circumstances.

Track the new route here: {tracking_url}

Best regards,
Autonomous Control Tower Team
                    """
                },
                "sms": "Shipment {tracking_number} rerouted. Expected to save {time_savings}h. New ETA: {new_eta}"
            },
            "risk_resolved": {
                "email": {
                    "subject": "Resolved: Risk on Shipment {tracking_number}",
                    "body": """
Dear {stakeholder_name},

The risk identified on shipment {tracking_number} has been successfully resolved.

Risk Type: {risk_type}
Resolution: {resolution_action}
Result: {resolution_result}
Current Status: Back on track

The shipment is now proceeding as planned with updated ETA: {eta}

Thank you for your patience.

Best regards,
Autonomous Control Tower Team
                    """
                }
            }
        }
    
    def _load_stakeholder_profiles(self) -> Dict[str, Any]:
        """Load stakeholder communication profiles"""
        return {
            "shipper": {
                "channels": ["email", "dashboard"],
                "detail_level": "high",
                "tone": "professional",
                "contact_preferences": {
                    "urgent": ["sms", "email"],
                    "normal": ["email", "dashboard"],
                    "informational": ["dashboard"]
                }
            },
            "consignee": {
                "channels": ["email", "sms", "dashboard"],
                "detail_level": "medium",
                "tone": "customer_friendly",
                "contact_preferences": {
                    "urgent": ["sms", "phone"],
                    "normal": ["email", "sms"],
                    "informational": ["email"]
                }
            },
            "carrier": {
                "channels": ["api", "email", "portal"],
                "detail_level": "technical",
                "tone": "formal",
                "contact_preferences": {
                    "urgent": ["api", "phone"],
                    "normal": ["api", "email"],
                    "informational": ["portal"]
                }
            },
            "customs_broker": {
                "channels": ["email", "portal", "api"],
                "detail_level": "high",
                "tone": "official",
                "contact_preferences": {
                    "urgent": ["phone", "email"],
                    "normal": ["email", "portal"],
                    "informational": ["portal"]
                }
            }
        }
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages"""
        message_type = message.get("message_type")
        
        if message_type == "notify_stakeholders":
            return await self._handle_notify_stakeholders(message)
        elif message_type == "generate_message":
            return await self._handle_generate_message(message)
        elif message_type == "send_bulk_notifications":
            return await self._handle_send_bulk_notifications(message)
        else:
            return {"error": f"Unknown message type: {message_type}"}
    
    async def _handle_notify_stakeholders(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stakeholder notification request"""
        content = message.get("content", {})
        shipment_id = content.get("shipment_id")
        notification_type = content.get("notification_type")
        data = content.get("data", {})
        urgency = content.get("urgency", "normal")
        
        # Get stakeholders for this shipment
        stakeholders = await self._get_shipment_stakeholders(shipment_id)
        
        if not stakeholders:
            return {"error": "No stakeholders found for shipment"}
        
        # Generate and send notifications
        results = []
        for stakeholder in stakeholders:
            result = await self._send_stakeholder_notification(
                stakeholder=stakeholder,
                shipment_id=shipment_id,
                notification_type=notification_type,
                data=data,
                urgency=urgency
            )
            results.append(result)
        
        # Log activity
        await self.log_activity(
            "stakeholder_notification",
            {
                "shipment_id": shipment_id,
                "notification_type": notification_type,
                "stakeholders_notified": len(stakeholders),
                "urgency": urgency,
                "successful": sum(1 for r in results if r.get("success"))
            }
        )
        
        return {
            "shipment_id": shipment_id,
            "notifications_sent": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _handle_generate_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered message"""
        content = message.get("content", {})
        stakeholder_type = content.get("stakeholder_type")
        message_type = content.get("message_type")
        context = content.get("context", {})
        
        try:
            # Generate message using AI
            ai_message = await self._generate_ai_message(
                stakeholder_type=stakeholder_type,
                message_type=message_type,
                context=context
            )
            
            return {
                "success": True,
                "message": ai_message,
                "stakeholder_type": stakeholder_type,
                "message_type": message_type
            }
            
        except Exception as e:
            # Fallback to template
            fallback_message = self._generate_fallback_message(
                stakeholder_type, message_type, context
            )
            
            return {
                "success": True,
                "message": fallback_message,
                "method": "template_fallback",
                "error": str(e)
            }
    
    async def _generate_ai_message(self, stakeholder_type: str, 
                                 message_type: str, context: Dict[str, Any]) -> str:
        """Generate AI-powered personalized message"""
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured")
        
        # Build prompt
        prompt = self._build_ai_prompt(stakeholder_type, message_type, context)
        
        # Call OpenAI API
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a supply chain communication specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _build_ai_prompt(self, stakeholder_type: str, message_type: str,
                        context: Dict[str, Any]) -> str:
        """Build AI prompt for message generation"""
        stakeholder_profile = self.stakeholder_profiles.get(stakeholder_type, {})
        
        prompt = f"""
        Generate a {stakeholder_profile.get('tone', 'professional')} 
        {message_type} message for a {stakeholder_type} in supply chain management.
        
        Context:
        {json.dumps(context, indent=2)}
        
        Requirements:
        1. Tone: {stakeholder_profile.get('tone', 'professional')}
        2. Detail level: {stakeholder_profile.get('detail_level', 'medium')}
        3. Include all relevant details from context
        4. Be clear and actionable
        5. Maintain professional supply chain terminology
        
        Generate the complete message body.
        """
        
        return prompt
    
    async def _send_stakeholder_notification(self, stakeholder: Dict[str, Any],
                                           shipment_id: int, notification_type: str,
                                           data: Dict[str, Any], urgency: str) -> Dict[str, Any]:
        """Send notification to a specific stakeholder"""
        stakeholder_type = stakeholder.get("type")
        contact_info = stakeholder.get("contact_info", {})
        
        # Get appropriate channels based on urgency
        channels = self._get_channels_for_urgency(stakeholder_type, urgency)
        
        # Generate message for each channel
        results = {}
        for channel in channels:
            if channel == "email" and contact_info.get("email"):
                message = await self._generate_channel_message(
                    channel, stakeholder_type, notification_type, data
                )
                result = await self._send_email(
                    to=contact_info["email"],
                    subject=message.get("subject", "Shipment Update"),
                    body=message.get("body", "")
                )
                results["email"] = result
            
            elif channel == "sms" and contact_info.get("phone"):
                message = await self._generate_channel_message(
                    channel, stakeholder_type, notification_type, data
                )
                result = await self._send_sms(
                    to=contact_info["phone"],
                    message=message.get("body", "")
                )
                results["sms"] = result
            
            elif channel == "api" and contact_info.get("api_endpoint"):
                result = await self._send_api_notification(
                    endpoint=contact_info["api_endpoint"],
                    data={"shipment_id": shipment_id, **data}
                )
                results["api"] = result
        
        return {
            "stakeholder_type": stakeholder_type,
            "channels_attempted": list(results.keys()),
            "success": any(results.values()),
            "results": results
        }
    
    def _get_channels_for_urgency(self, stakeholder_type: str, urgency: str) -> List[str]:
        """Get communication channels based on urgency"""
        profile = self.stakeholder_profiles.get(stakeholder_type, {})
        preferences = profile.get("contact_preferences", {})
        return preferences.get(urgency, ["email"])
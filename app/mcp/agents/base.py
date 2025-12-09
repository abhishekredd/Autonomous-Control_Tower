from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
from app.core.redis import redis_client
from app.core.database import AsyncSessionLocal

class BaseAgent(ABC):
    """Base class for all MCP agents"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.is_running = False
        self.message_queue = asyncio.Queue()
        self.context_store: Dict[str, Any] = {}
        
    async def start(self):
        """Start the agent"""
        self.is_running = True
        print(f"🚀 Starting {self.agent_type} agent: {self.agent_id}")
        
        # Subscribe to relevant Redis channels
        await self._setup_subscriptions()
        
        # Start message processing loop
        asyncio.create_task(self._message_loop())
        
    async def stop(self):
        """Stop the agent"""
        self.is_running = False
        print(f"🛑 Stopping {self.agent_type} agent: {self.agent_id}")
        
    async def _setup_subscriptions(self):
        """Setup Redis subscriptions for this agent"""
        # Base subscriptions
        channels = [
            f"agent:{self.agent_id}:messages",
            f"agent:{self.agent_type}:broadcast"
        ]
        
        # Agent-specific subscriptions
        agent_channels = self._get_agent_channels()
        channels.extend(agent_channels)
        
        for channel in channels:
            await redis_client.subscribe(channel)
            print(f"📡 {self.agent_id} subscribed to: {channel}")
    
    def _get_agent_channels(self) -> List[str]:
        """Get agent-specific Redis channels to subscribe to"""
        return []
    
    async def _message_loop(self):
        """Main message processing loop"""
        while self.is_running:
            try:
                # Process incoming messages
                await self._process_incoming_messages()
                
                # Check for scheduled tasks
                await self._check_scheduled_tasks()
                
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                print(f"Error in {self.agent_id} message loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_incoming_messages(self):
        """Process incoming Redis messages"""
        # This would check Redis pub/sub for new messages
        # For now, simulate message processing
        pass
    
    async def _check_scheduled_tasks(self):
        """Check for scheduled tasks that need to run"""
        # Override in subclasses for scheduled tasks
        pass
    
    async def send_message(self, recipient_agent: str, message_type: str,
                         content: Dict[str, Any], context_id: Optional[str] = None):
        """Send a message to another agent"""
        message = {
            "sender": self.agent_id,
            "recipient": recipient_agent,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "context_id": context_id or f"ctx_{datetime.utcnow().timestamp()}"
        }
        
        await redis_client.publish(
            f"agent:{recipient_agent}:messages",
            json.dumps(message)
        )
        
        print(f"📨 {self.agent_id} → {recipient_agent}: {message_type}")
    
    async def broadcast_message(self, message_type: str, content: Dict[str, Any]):
        """Broadcast a message to all agents"""
        message = {
            "sender": self.agent_id,
            "message_type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "broadcast": True
        }
        
        await redis_client.publish(
            "agent:broadcast:all",
            json.dumps(message)
        )
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming message (abstract method)"""
        pass
    
    async def get_database_session(self):
        """Get a database session for this agent"""
        return AsyncSessionLocal()
    
    async def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log agent activity"""
        log_entry = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "activity_type": activity_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await redis_client.publish(
            "agent:activity:logs",
            json.dumps(log_entry)
        )
        
        # Also store in database
        async with AsyncSessionLocal() as session:
            # In production, store in agent_activities table
            pass
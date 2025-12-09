from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, List
import json
import asyncio
from datetime import datetime
from app.core.redis import redis_client

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, shipment_id: str):
        await websocket.accept()
        if shipment_id not in self.active_connections:
            self.active_connections[shipment_id] = []
        self.active_connections[shipment_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, shipment_id: str):
        if shipment_id in self.active_connections:
            self.active_connections[shipment_id].remove(websocket)
            if not self.active_connections[shipment_id]:
                del self.active_connections[shipment_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_shipment(self, shipment_id: str, message: dict):
        if shipment_id in self.active_connections:
            message_json = json.dumps(message)
            for connection in self.active_connections[shipment_id]:
                try:
                    await connection.send_text(message_json)
                except:
                    self.disconnect(connection, shipment_id)

manager = ConnectionManager()

@router.websocket("/ws/shipments/{shipment_id}")
async def websocket_shipment_endpoint(websocket: WebSocket, shipment_id: str):
    await manager.connect(websocket, shipment_id)
    
    # Subscribe to Redis channel for this shipment
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"shipment_updates:{shipment_id}")
    
    try:
        while True:
            # Listen for Redis messages
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if message:
                await websocket.send_json(json.loads(message['data']))
            else:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Also listen for client messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                # Handle client messages if needed
            except asyncio.TimeoutError:
                continue
                
    except WebSocketDisconnect:
        await pubsub.unsubscribe(f"shipment_updates:{shipment_id}")
        manager.disconnect(websocket, shipment_id)

@router.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Subscribe to dashboard updates
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("dashboard_updates")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30.0)
            if message:
                await websocket.send_json(json.loads(message['data']))
            else:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        await pubsub.unsubscribe("dashboard_updates")
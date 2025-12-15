from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload
from app.models.shipment import Shipment, ShipmentStatus, ShipmentEvent, ShipmentRoute
from app.models.risk import Risk, RiskStatus
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentInDB
from app.core.redis import redis_client
import json

class ShipmentService:
    """Service for shipment management and operations"""
    
    async def create_shipment(self, shipment_data: ShipmentCreate, session: AsyncSession) -> Shipment:
        """Create a new shipment"""
        def _to_naive(dt: Optional[datetime]) -> Optional[datetime]:
            if dt is None:
                return None
            # If tz-aware, convert to UTC then drop tzinfo to store as naive
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        shipment = Shipment(
            tracking_number=shipment_data.tracking_number,
            reference_number=shipment_data.reference_number,
            origin=shipment_data.origin,
            destination=shipment_data.destination,
            mode=shipment_data.mode,
            weight=shipment_data.weight,
            volume=shipment_data.volume,
            value=shipment_data.value,
            estimated_departure=_to_naive(shipment_data.estimated_departure),
            estimated_arrival=_to_naive(shipment_data.estimated_arrival),
            shipper=shipment_data.shipper,
            carrier=shipment_data.carrier,
            consignee=shipment_data.consignee,
            status=ShipmentStatus.PENDING,
            shipment_metadata={
                "created_by": "api",
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        session.add(shipment)
        # Ensure any tz-aware datetimes on the instance are normalized to tz-naive before flush
        for _field in ("estimated_departure", "estimated_arrival", "actual_departure", "actual_arrival", "last_risk_check"):
            val = getattr(shipment, _field, None)
            if isinstance(val, datetime) and val.tzinfo is not None:
                setattr(shipment, _field, val.astimezone(timezone.utc).replace(tzinfo=None))

        await session.commit()
        await session.refresh(shipment)
        
        # Create initial event
        event = ShipmentEvent(
            shipment_id=shipment.id,
            event_type="created",
            location=shipment.origin,
            description=f"Shipment created with tracking number {shipment.tracking_number}",
            timestamp=datetime.utcnow(),
            metadata={"source": "api"}
        )
        
        session.add(event)
        await session.commit()
        
        # Publish to Redis for real-time updates
        await redis_client.publish(
            "shipment_created",
            json.dumps({
                "shipment_id": shipment.id,
                "tracking_number": shipment.tracking_number,
                "origin": shipment.origin,
                "destination": shipment.destination,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        return shipment
    
    async def get_shipment(self, shipment_id: int, session: AsyncSession) -> Optional[Shipment]:
        """Get a shipment by ID"""
        result = await session.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_shipment_with_relations(self, shipment_id: int, session: AsyncSession) -> Optional[Shipment]:
        """Get a shipment with all related data"""
        result = await session.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.risks),
                selectinload(Shipment.events),
                selectinload(Shipment.simulations)
            )
            .where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()
    
    async def get_shipments(self,
            skip: int = 0,
            limit: int = 100,
            status: Optional[str] = None,
            at_risk: Optional[bool] = None,
            db: AsyncSession = None
        ) -> List[Shipment]:
            """Get shipments with filtering"""
            query = select(Shipment)

            if status:
                query = query.where(Shipment.status == ShipmentStatus(status))

            if at_risk is not None:
                query = query.where(Shipment.is_at_risk == at_risk)

            query = query.offset(skip).limit(limit).order_by(desc(Shipment.created_at))

            result = await db.execute(query)
            return result.scalars().all()
    
    async def update_shipment(self, shipment_id: int, update_data: ShipmentUpdate,
                            session: AsyncSession) -> Optional[Shipment]:
        """Update a shipment"""
        shipment = await self.get_shipment(shipment_id, session)
        
        if not shipment:
            return None
        
        # Update fields
        def _to_naive(dt: Optional[datetime]) -> Optional[datetime]:
            if dt is None:
                return None
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt

        for field, value in update_data.dict(exclude_unset=True).items():
            if field == "shipment_metadata" and value:
                shipment.shipment_metadata = {**shipment.shipment_metadata, **value}
            elif hasattr(shipment, field):
                # normalize datetime fields if present
                if isinstance(value, datetime):
                    value = _to_naive(value)
                setattr(shipment, field, value)
        
        shipment.updated_at = datetime.utcnow()
        # Normalize any tz-aware datetimes before commit
        for _field in ("estimated_departure", "estimated_arrival", "actual_departure", "actual_arrival", "last_risk_check"):
            val = getattr(shipment, _field, None)
            if isinstance(val, datetime) and val.tzinfo is not None:
                setattr(shipment, _field, val.astimezone(timezone.utc).replace(tzinfo=None))

        await session.commit()
        await session.refresh(shipment)
        
        # Create update event
        event = ShipmentEvent(
            shipment_id=shipment.id,
            event_type="updated",
            location=shipment.current_location or shipment.origin,
            description="Shipment details updated",
            timestamp=datetime.utcnow(),
            metadata={"update_fields": list(update_data.dict(exclude_unset=True).keys())}
        )
        
        session.add(event)
        await session.commit()
        
        # Publish update
        await redis_client.publish(
            "shipment_updated",
            json.dumps({
                "shipment_id": shipment.id,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status.value,
                "current_location": shipment.current_location,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        return shipment
    
    async def update_shipment_location(self, shipment_id: int, location: str, session: AsyncSession,
                                     port: Optional[str] = None
                                     ) -> bool:
        """Update shipment location"""
        shipment = await self.get_shipment(shipment_id, session)
        
        if not shipment:
            return False
        
        previous_location = shipment.current_location
        shipment.current_location = location
        
        if port:
            shipment.current_port = port
        
        # Create location event
        event = ShipmentEvent(
            shipment_id=shipment.id,
            event_type="location_update",
            location=location,
            description=f"Location updated: {previous_location or 'N/A'} → {location}",
            timestamp=datetime.utcnow(),
            metadata={
                "previous_location": previous_location,
                "new_location": location,
                "port": port
            }
        )
        
        session.add(event)
        await session.commit()
        
        # Publish location update
        await redis_client.publish(
            f"shipment_updates:{shipment_id}",
            json.dumps({
                "type": "location_update",
                "shipment_id": shipment_id,
                "location": location,
                "port": port,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        return True
    
    async def add_shipment_event(self, shipment_id: int, event_type: str,
                               location: str, description: str,
                               session: AsyncSession,
                               metadata: Optional[Dict] = None
                               ) -> bool:
        """Add an event to a shipment"""
        event = ShipmentEvent(
            shipment_id=shipment_id,
            event_type=event_type,
            location=location,
            description=description,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        session.add(event)
        await session.commit()
        
        # Publish event
        await redis_client.publish(
            f"shipment_updates:{shipment_id}",
            json.dumps({
                "type": "event",
                "shipment_id": shipment_id,
                "event_type": event_type,
                "description": description,
                "timestamp": datetime.utcnow().isoformat()
            })
        )
        
        return True
    
    async def trigger_risk_check(self, shipment_id: int, session: AsyncSession) -> bool:
        """Trigger a risk check for a shipment"""
        shipment = await self.get_shipment(shipment_id, session)
        
        if not shipment:
            return False
        
        # Update last risk check time
        shipment.last_risk_check = datetime.utcnow()
        await session.commit()
        
        # Publish risk check event
        await redis_client.publish(
            "risk_check_requested",
            json.dumps({
                "shipment_id": shipment_id,
                "timestamp": datetime.utcnow().isoformat(),
                "trigger": "manual"
            })
        )
        
        # Create event
        await self.add_shipment_event(
            shipment_id=shipment_id,
            event_type="risk_check",
            location=shipment.current_location or shipment.origin,
            description="Manual risk check triggered",
            session=session
        )
        
        return True
    
    async def get_shipment_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """Get shipment statistics"""
        # Total shipments
        total_result = await session.execute(
            select(func.count(Shipment.id))
        )
        total = total_result.scalar()
        
        # By status
        status_result = await session.execute(
            select(Shipment.status, func.count(Shipment.id))
            .group_by(Shipment.status)
        )
        by_status = {status.value: count for status, count in status_result.all()}
        
        # At risk
        at_risk_result = await session.execute(
            select(func.count(Shipment.id))
            .where(Shipment.is_at_risk == True)
        )
        at_risk = at_risk_result.scalar()
        
        # Recent activity
        recent_result = await session.execute(
            select(ShipmentEvent)
            .order_by(desc(ShipmentEvent.timestamp))
            .limit(10)
        )
        recent_events = recent_result.scalars().all()
        
        return {
            "total_shipments": total,
            "by_status": by_status,
            "at_risk": at_risk,
            "at_risk_percentage": (at_risk / total * 100) if total > 0 else 0,
            "recent_events": [
                {
                    "shipment_id": event.shipment_id,
                    "event_type": event.event_type,
                    "description": event.description,
                    "timestamp": event.timestamp.isoformat()
                }
                for event in recent_events
            ]
        }
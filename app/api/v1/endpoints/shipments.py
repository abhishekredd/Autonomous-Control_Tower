from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentInDB, ShipmentWithRelations
from app.services.shipment_service import ShipmentService

router = APIRouter()
shipment_service = ShipmentService()

@router.post("/", response_model=ShipmentInDB)
async def create_shipment(
    shipment: ShipmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new shipment"""
    return await shipment_service.create_shipment(shipment, db)

@router.get("/", response_model=List[ShipmentInDB])
async def get_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    at_risk: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all shipments with optional filters"""
    return await shipment_service.get_shipments(skip, limit, status, at_risk, db)

@router.get("/{shipment_id}", response_model=ShipmentWithRelations)
async def get_shipment(
    shipment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific shipment with all relations"""
    shipment = await shipment_service.get_shipment_with_relations(shipment_id, db)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.put("/{shipment_id}", response_model=ShipmentInDB)
async def update_shipment(
    shipment_id: int,
    shipment_update: ShipmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a shipment"""
    shipment = await shipment_service.update_shipment(shipment_id, shipment_update, db)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@router.post("/{shipment_id}/trigger-risk-check")
async def trigger_risk_check(
    shipment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger risk check for a shipment"""
    success = await shipment_service.trigger_risk_check(shipment_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Shipment not found or check failed")
    return {"message": "Risk check triggered successfully"}

@router.get("/{shipment_id}/realtime")
async def get_realtime_updates(
    shipment_id: int
):
    """WebSocket endpoint for real-time shipment updates"""
    # This would be handled by the WebSocket router
    pass
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import get_current_user
from app.services.shipment_service import ShipmentService
from app.services.risk_service import RiskService

async def get_db() -> Generator:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_shipment_service() -> ShipmentService:
    """Dependency to get shipment service"""
    return ShipmentService()

async def get_risk_service() -> RiskService:
    """Dependency to get risk service"""
    return RiskService()

async def verify_shipment_access(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Verify user has access to shipment"""
    shipment_service = ShipmentService()
    shipment = await shipment_service.get_shipment(shipment_id, db)
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # In production, add more sophisticated access control
    # For now, just return shipment
    return {"shipment": shipment, "user": current_user}

async def verify_risk_access(
    risk_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Verify user has access to risk"""
    risk_service = RiskService()
    risk = await risk_service.get_risk(risk_id, db)
    
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk not found"
        )
    
    # Verify user has access to the related shipment
    shipment_service = ShipmentService()
    shipment = await shipment_service.get_shipment(risk.shipment_id, db)
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Related shipment not found"
        )
    
    return {"risk": risk, "shipment": shipment, "user": current_user}

# Pagination dependency
def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """Get pagination parameters"""
    return {"skip": skip, "limit": min(limit, 1000)}

# Filter dependencies for shipments
def get_shipment_filters(
    status: Optional[str] = None,
    at_risk: Optional[bool] = None,
    mode: Optional[str] = None
) -> dict:
    """Get shipment filter parameters"""
    filters = {}
    if status:
        filters["status"] = status
    if at_risk is not None:
        filters["at_risk"] = at_risk
    if mode:
        filters["mode"] = mode
    return filters

# Filter dependencies for risks
def get_risk_filters(
    shipment_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    risk_type: Optional[str] = None
) -> dict:
    """Get risk filter parameters"""
    filters = {}
    if shipment_id:
        filters["shipment_id"] = shipment_id
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
    if risk_type:
        filters["risk_type"] = risk_type
    return filters
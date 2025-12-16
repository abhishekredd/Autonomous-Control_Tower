from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.schemas.risk import RiskCreate, RiskUpdate, RiskInDB
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService

router = APIRouter()
risk_service = RiskService()
shipment_service = ShipmentService()

@router.get("/", response_model=List[RiskInDB])
async def get_risks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    shipment_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all risks with optional filters"""
    try:
        risks = await risk_service.get_risks(
            skip=skip,
            limit=limit,
            shipment_id=shipment_id,
            status=status,
            severity=severity,
            session=db
        )
        print(f"[DEBUG] Returning {len(risks)} risks")
        return risks
    except Exception as e:
        import traceback
        print("[ERROR] Exception in /risks:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{risk_id}", response_model=RiskInDB)
async def get_risk(
    risk_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific risk"""
    try:
        risk = await risk_service.get_risk(risk_id, db)
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        return risk
    except Exception as e:
        import traceback
        print("[ERROR] Exception in /risks/{risk_id}:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=RiskInDB, status_code=status.HTTP_201_CREATED)
async def create_risk(
    risk: RiskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Create a new risk (admin only)"""
    try:
        # Verify shipment exists
        shipment = await shipment_service.get_shipment(risk.shipment_id, db)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return await risk_service.create_risk(risk, db)
    except Exception as e:
        import traceback
        print("[ERROR] Exception in POST /risks:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{risk_id}", response_model=RiskInDB)
async def update_risk(
    risk_id: int,
    risk_update: RiskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Update a risk (admin only)"""
    try:
        risk = await risk_service.update_risk(risk_id, risk_update, db)
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        return risk
    except Exception as e:
        import traceback
        print("[ERROR] Exception in PUT /risks/{risk_id}:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk(
    risk_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Delete a risk (admin only)"""
    try:
        success = await risk_service.delete_risk(risk_id, db)
        if not success:
            raise HTTPException(status_code=404, detail="Risk not found")
    except Exception as e:
        import traceback
        print("[ERROR] Exception in DELETE /risks/{risk_id}:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{risk_id}/mitigate")
async def mitigate_risk(
    risk_id: int,
    mitigation_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Apply mitigation to a risk"""
    try:
        risk = await risk_service.get_risk(risk_id, db)
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        # Apply mitigation
        updated_risk = await risk_service.apply_mitigation(
            risk_id=risk_id,
            mitigation_data=mitigation_data,
            session=db
        )
        return {
            "message": "Mitigation applied successfully",
            "risk": updated_risk
        }
    except Exception as e:
        import traceback
        print("[ERROR] Exception in POST /risks/{risk_id}/mitigate:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shipment/{shipment_id}", response_model=List[RiskInDB])
async def get_shipment_risks(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all risks for a specific shipment"""
    try:
        risks = await risk_service.get_shipment_risks(shipment_id, db)
        return risks
    except Exception as e:
        import traceback
        print("[ERROR] Exception in GET /risks/shipment/{shipment_id}:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats")
async def get_risk_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get risk statistics for dashboard"""
    try:
        stats = await risk_service.get_risk_statistics(db)
        return stats
    except Exception as e:
        import traceback
        print("[ERROR] Exception in GET /risks/dashboard/stats:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

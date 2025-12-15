from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.schemas.simulation import SimulationCreate, SimulationInDB
from app.services.simulation_service import SimulationService
from app.services.shipment_service import ShipmentService

import logging
logger = logging.getLogger(__name__)

router = APIRouter()
simulation_service = SimulationService()
shipment_service = ShipmentService()

# ------------------------------
# Request models
# ------------------------------

class MitigationRequest(BaseModel):
    shipment_id: int
    risk_data: Dict[str, Any]

# ------------------------------
# Endpoints
# ------------------------------

@router.post("/", response_model=SimulationInDB)
async def create_simulation(
    simulation: SimulationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create and run a new simulation"""
    logger.info("Received simulation request: %s", simulation.dict())
    shipment = await shipment_service.get_shipment(simulation.shipment_id, db)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Create simulation record
    simulation_record = await simulation_service.create_simulation(simulation, db)
    logger.info("Created simulation record with id=%s", simulation_record.id)

    # Run simulation in background
    background_tasks.add_task(
        simulation_service.run_simulation_task,
        simulation_record.id,
        simulation.parameters
    )
    logger.info("Background task scheduled for simulation %s", simulation_record.id)

    return simulation_record

@router.get("/{simulation_id}", response_model=SimulationInDB)
async def get_simulation(
    simulation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific simulation"""
    simulation = await simulation_service.get_simulation(simulation_id, db)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation

@router.get("/shipment/{shipment_id}", response_model=List[SimulationInDB])
async def get_shipment_simulations(
    shipment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all simulations for a shipment"""
    simulations = await simulation_service.get_shipment_simulations(shipment_id, db)
    return simulations

@router.post("/{simulation_id}/rerun")
async def rerun_simulation(
    simulation_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin"))
):
    """Rerun a simulation"""
    simulation = await simulation_service.get_simulation(simulation_id, db)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Reset simulation status
    simulation = await simulation_service.reset_simulation(simulation_id, db)

    # Rerun in background
    background_tasks.add_task(
        simulation_service.run_simulation_task,
        simulation_id,
        simulation.parameters
    )

    return {"message": "Simulation rerun started", "simulation_id": simulation_id}

@router.post("/mitigation/run")
async def run_mitigation_simulation(
    request: MitigationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Run mitigation simulation for a risk"""
    shipment = await shipment_service.get_shipment(request.shipment_id, db)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # Create simulation
    simulation_data = SimulationCreate(
        shipment_id=request.shipment_id,
        simulation_type="mitigation_analysis",
        parameters={
            "risk_data": request.risk_data,
            "simulation_type": "mitigation_analysis",
            "scenario": "risk_mitigation"
        },
        scenario_description=f"Mitigation analysis for risk on shipment {request.shipment_id}"
    )

    simulation_record = await simulation_service.create_simulation(simulation_data, db)

    # Run in background
    background_tasks.add_task(
        simulation_service.run_mitigation_simulation,
        simulation_record.id,
        request.shipment_id,
        request.risk_data
    )

    return {
        "message": "Mitigation simulation started",
        "simulation_id": simulation_record.id
    }

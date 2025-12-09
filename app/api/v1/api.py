from fastapi import APIRouter
from app.api.v1.endpoints import shipments, risks, simulations

api_router = APIRouter()

api_router.include_router(shipments.router, prefix="/shipments", tags=["shipments"])
api_router.include_router(risks.router, prefix="/risks", tags=["risks"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
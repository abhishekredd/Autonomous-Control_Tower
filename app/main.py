from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.api.v1.api import api_router
from app.api.websocket import router as websocket_router
from app.core.config import settings
from app.core.database import engine, Base
from app.core.celery_app import celery_app
from app.services.orchestrator import CentralOrchestrator

app = FastAPI()

# CORS: allow frontend to call API. Limit origins in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # restrict to your Streamlit domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API under /api/v1
app.include_router(api_router, prefix="/api/v1")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Autonomous Control Tower...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize central orchestrator
    orchestrator = CentralOrchestrator()
    asyncio.create_task(orchestrator.initialize())
    app.state.orchestrator = orchestrator
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Autonomous Control Tower...")

app = FastAPI(
    title="Autonomous Control Tower API",
    description="AI-powered supply chain management system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/ws")

@app.get("/")
async def root():
    return {"message": "Autonomous Control Tower API", "status": "operational"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "database": "connected",
            "redis": "connected",
            "rabbitmq": "connected"
        }
    }
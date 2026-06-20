from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import v1_router
from app.services.storage_service import get_project_root
from app.core.scheduler import start_scheduler, stop_scheduler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Background Scheduler
    start_scheduler()
    yield
    # Shutdown: Stop Background Scheduler
    stop_scheduler()

app = FastAPI(
    title="AI Paper Multi-Agent Backend",
    description="Backend API Gateway for AI Paper Multi-Agent System",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/data", StaticFiles(directory=str(get_project_root() / "data")), name="static-data")

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "AI Paper Multi-Agent Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


from fastapi import FastAPI, Depends, HTTPException, status
import logging
from pydantic import BaseModel
from typing import Optional
from app.pipeline import run_daily_summary_pipeline
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "../../../backend/.env"))

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:tamnguyen234@localhost:3306/ai_papers")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_paper_agent")

app = FastAPI(
    title="Daily Paper Agent",
    description="Agent for fetching, translating, and synthesizing TTS for daily trending papers.",
    version="0.1.0"
)

class RunPipelineRequest(BaseModel):
    digest_date: Optional[str] = None
    skip_audio: bool = False

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "daily_paper_agent"}

@app.post("/api/v1/pipeline/run")
def run_pipeline(payload: RunPipelineRequest, db=Depends(get_db)):
    try:
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # Parse date if provided
        import datetime
        target_date = None
        if payload.digest_date:
            target_date = datetime.datetime.strptime(payload.digest_date, "%Y-%m-%d").date()

        result = run_daily_summary_pipeline(
            db=db,
            digest_date=target_date,
            project_root=project_root,
            skip_audio=payload.skip_audio
        )
        return {"status": "success", "data": result.model_dump() if hasattr(result, "model_dump") else result.dict()}
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

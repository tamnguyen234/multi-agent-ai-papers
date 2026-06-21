from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models.digest import Digest
from app.schemas.digest_schema import DigestResponse

router = APIRouter()

@router.post("/trigger")
def trigger_daily_digest(db: Session = Depends(get_db)):
    """Manually trigger daily digest aggregation."""
    return {"message": "Daily digest job started"}

@router.get("/latest")
def get_latest_digest(db: Session = Depends(get_db)):
    """Get latest aggregated digest papers list."""
    return {"digest": []}

@router.get("/today", response_model=DigestResponse)
def get_today_digest(db: Session = Depends(get_db)):
    """Retrieve today's digest, with papers sorted by rank_position ascending."""
    today = datetime.now().date()
    digest = db.query(Digest).filter(Digest.digest_date == today).first()
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No digest found for today."
        )
    # Sort papers by rank_position ascending
    sorted_papers = sorted(digest.digest_papers, key=lambda dp: dp.rank_position)
    return {
        "id": digest.id,
        "digest_date": digest.digest_date,
        "papers": sorted_papers
    }

@router.get("/{digest_id}", response_model=DigestResponse)
def get_digest_detail(digest_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed information of a single digest by its database ID."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if not digest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digest with ID {digest_id} not found."
        )
    # Sort papers by rank_position ascending
    sorted_papers = sorted(digest.digest_papers, key=lambda dp: dp.rank_position)
    return {
        "id": digest.id,
        "digest_date": digest.digest_date,
        "papers": sorted_papers
    }

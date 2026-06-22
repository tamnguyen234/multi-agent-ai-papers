from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from app.db.database import get_db
from app.db.models.paper import Paper
from app.db.models.user import User
from app.schemas.paper_schema import PaperResponse, AudioAbstractRequest, LazyAudioAbstractResponse
from app.core.security import get_current_user_optional
from app.services.audio_abstract_service import generate_audio_for_paper_summary

router = APIRouter()

@router.get("/", response_model=List[PaperResponse])
def get_papers(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve list of papers, sorted by published desc (fallback created_at desc) with pagination and search."""
    query = db.query(Paper)
    
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Paper.title).like(search_term),
                func.lower(Paper.abstract_en).like(search_term)
            )
        )
        
    papers = query.order_by(Paper.published.desc(), Paper.created_at.desc()).offset(skip).limit(limit).all()
    return papers

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper_detail(paper_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed information of a single paper by its database ID."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found."
        )
    return paper

@router.post("/{paper_id}/audio-abstract", response_model=LazyAudioAbstractResponse)
def generate_paper_audio_abstract(
    paper_id: int,
    payload: AudioAbstractRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Exposes lazy/on-demand audio abstract generation for a specific paper.
    If force=True, require authentication. If force=False, it is public.
    """
    # 1. Authentication check for force-regeneration
    if payload.force:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication is required to force regenerate the audio abstract."
            )
            
    # 2. Fetch Paper
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {paper_id} not found."
        )
        
    # 3. Call Service Layer
    try:
        result = generate_audio_for_paper_summary(
            db=db,
            paper=paper,
            force=payload.force,
            voice=payload.voice,
            language=payload.language
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error generating audio abstract: {str(e)}"
        )


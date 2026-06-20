from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.core.security import get_current_user
from app.schemas.auth_schema import UserResponse, NotificationUpdate

router = APIRouter()

@router.get("/me")
def get_user_profile(db: Session = Depends(get_db)):
    """Fetch profile details of active user."""
    return {"id": 1, "email": "user@example.com", "name": "Demo User"}

@router.put("/me/settings")
def update_user_settings(receive_digest_emails: bool, db: Session = Depends(get_db)):
    """Configure email notification settings."""
    return {"receive_digest_emails": receive_digest_emails}

@router.patch("/me/notification", response_model=UserResponse)
def update_notification(
    update_in: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update notification settings for the current logged-in user."""
    current_user.noti_daily = update_in.noti_daily
    db.commit()
    db.refresh(current_user)
    return current_user

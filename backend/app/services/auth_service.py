from sqlalchemy.orm import Session

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str):
        """Authenticate user login."""

    def create_user(self, user_schema):
        """Create new user account."""

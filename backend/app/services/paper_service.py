from sqlalchemy.orm import Session

class PaperService:
    def __init__(self, db: Session):
        self.db = db

    def get_papers(self, skip: int = 0, limit: int = 100):
        """Retrieve list of downloaded papers."""

    def get_paper_by_id(self, paper_id: int):
        """Retrieve details of a specific paper."""

    def create_paper_entry(self, paper_data):
        """Save metadata of a new AI paper."""

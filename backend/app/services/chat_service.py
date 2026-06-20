from sqlalchemy.orm import Session

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def post_chat_message(self, paper_id: int, user_message: str):
        """Send message to Q&A Agent and retrieve AI response."""
        pass

    def get_chat_history(self, paper_id: int, user_id: int):
        """Retrieve conversation logs for a paper."""
        pass

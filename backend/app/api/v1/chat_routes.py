from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.paper import Paper
from app.db.models.chat import ChatSession, ChatMessage
from app.core.security import get_current_user
from app.core.config import settings
from app.services.qa_client import ask_question
from app.schemas.chat_schema import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatAskResponse
)

router = APIRouter()

def _build_recent_qa_history(messages: List[ChatMessage], limit: int = 3) -> List[dict]:
    """Return the last completed user/assistant exchanges in Agent2 history shape."""
    history = []
    pending_question = None

    for message in messages:
        if message.role == "user":
            pending_question = message.content
        elif message.role == "assistant" and pending_question:
            history.append({"q": pending_question, "a": message.content})
            pending_question = None

    return history[-limit:]

# --- New Route Endpoints for Task 9 ---

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    session_in: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat session for a user and paper.
    If session already exists, return the existing session.
    """
    # Verify paper exists
    paper = db.query(Paper).filter(Paper.id == session_in.paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper with ID {session_in.paper_id} not found."
        )
        
    # Check if a session already exists for this user-paper pair
    existing_session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.paper_id == session_in.paper_id
    ).first()
    
    if existing_session:
        return existing_session
        
    # Create new session
    new_session = ChatSession(
        user_id=current_user.id,
        paper_id=session_in.paper_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/papers/{paper_id}/session", response_model=ChatSessionResponse)
def get_session_by_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the active chat session for a user and paper. Raise 404 if not found."""
    session = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.paper_id == paper_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chat session found for paper ID {paper_id} and current user."
        )
    return session

@router.post("/messages", response_model=ChatAskResponse)
def post_chat_message(
    message_in: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a user question, query the Q&A Agent, save the response, and return the interaction.
    Transaction rolls back if the Q&A Agent call fails.
    """
    # Check that session exists
    session = db.query(ChatSession).filter(ChatSession.id == message_in.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session with ID {message_in.session_id} not found."
        )
        
    # Verify ownership of the session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to post messages to this chat session."
        )
        
    # Get paper details
    paper = db.query(Paper).filter(Paper.id == session.paper_id).first()
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper associated with this chat session not found."
        )

    previous_messages = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == session.id
    ).order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc()).all()
    qa_history = _build_recent_qa_history(previous_messages, limit=3)
        
    # 1. Create and add user message (flushed but not committed)
    user_message = ChatMessage(
        chat_session_id=session.id,
        role="user",
        content=message_in.question
    )
    db.add(user_message)
    
    try:
        db.flush()  # assign ID to user_message
        
        # 2. Call Q&A Agent
        payload = {
            "paper_id": paper.id,
            "pdf_path": paper.pdf_path,
            "title": paper.title,
            "abstract": paper.abstract,
            "summary": paper.summary_vi,
            "question": message_in.question,
            "external_id": paper.external_id,
            "history": qa_history
        }
        agent_res = ask_question(payload)
        
        # 3. Create and add assistant response message
        assistant_message = ChatMessage(
            chat_session_id=session.id,
            role="assistant",
            content=agent_res["answer"]
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing Q&A request: {str(e)}"
        )
        
    return {
        "session": session,
        "user_message": user_message,
        "assistant_message": assistant_message,
        "qa_mode": agent_res.get("mode", "real"),
        "sources": agent_res.get("sources", [])
    }

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get message history for a chat session in chronological order (created_at asc)."""
    # Check session exists
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session with ID {session_id} not found."
        )
        
    # Verify ownership of the session
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view messages from this chat session."
        )
        
    # Fetch messages in chronological order
    messages = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return messages



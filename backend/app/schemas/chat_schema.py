from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List

class ChatSessionCreate(BaseModel):
    paper_id: int

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    paper_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    session_id: int
    question: str = Field(..., min_length=1)

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str

    created_at: datetime

    class Config:
        from_attributes = True

class ChatAskResponse(BaseModel):
    session: ChatSessionResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    qa_mode: str
    sources: List[Any] = []

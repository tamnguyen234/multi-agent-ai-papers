import os
import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Any
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models.user import User
from app.db.models.chat import ChatMessage, ChatSession
from app.core.security import get_current_user
from app.services.tts_client import synthesize_text
from app.services import storage_service

router = APIRouter()

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    import re
    import unicodedata
    
    # 1. Bỏ prefix `[Dự phòng - Ollama offline]` (case-insensitive)
    text = re.sub(r"^\[Dự phòng - Ollama offline\]\s*", "", text, flags=re.IGNORECASE)
    
    # 2. Bỏ markdown table và dòng chứa nhiều ký tự |---|, ||||, ----
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if (
            "||" in stripped
            or "|---|" in stripped
            or "---" in stripped
            or stripped.count("|") >= 2
        ):
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    
    # 3. Bỏ tag <br>
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    
    # 4. Bỏ ký tự điều khiển/ký tự lạ, giữ lại Unicode Vietnamese
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\r\n\t")
    
    # 5. Cắt text còn khoảng 1200 ký tự
    text = text[:1200].strip()
    return text

class TTSChatMessageRequest(BaseModel):
    message_id: int
    voice: Optional[str] = "vi_female"
    language: Optional[str] = "vi"
    speed: Optional[float] = 1.0

@router.post("/chat-message")
def convert_chat_message_to_speech(
    payload: TTSChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synthesize speech for a chat assistant message.
    Requires authentication, validates session ownership, prevents duplicate generation,
    and handles file cleanups if DB operations fail.
    """
    # 1. Fetch ChatMessage
    message = db.query(ChatMessage).filter(ChatMessage.id == payload.message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat message with ID {payload.message_id} not found."
        )
        
    # 2. Fetch ChatSession and enforce ownership
    session = db.query(ChatSession).filter(ChatSession.id == message.chat_session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated chat session not found."
        )
        
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat message's audio."
        )
        
    # 3. Only allow assistant role
    if message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS can only be generated for assistant responses."
        )
        
    # 4. Check if audio already exists
    if message.tts_path:
        project_root = storage_service.get_project_root()
        full_path = project_root / message.tts_path
        if os.path.exists(full_path):
            # Explicitly compute URL from path (do not rely on ORM property serialization)
            computed_url = storage_service.path_to_url(message.tts_path)
            return {
                "message_id": message.id,
                "tts_path": message.tts_path,
                "tts_url": computed_url,
                "tts_timestamps": message.tts_timestamps or [],
                "duration_seconds": 1.0,
                "mode": "existing"
            }
            
    # 5. Sanitize text and map voice
    sanitized_text = sanitize_text(message.content)
    if not sanitized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sanitized text is empty. Cannot synthesize speech."
        )
        
    voice_map = {
        "vi_female": "Ngọc Linh",
        "vi_male": "Gia Bảo"
    }
    target_voice = voice_map.get(payload.voice, "Ngọc Linh")
    
    agent_payload = {
        "text": sanitized_text,
        "voice": target_voice,
        "language": payload.language,
        "speed": payload.speed
    }
    
    agent_res = synthesize_text(agent_payload)
    
    # 6. Decode base64 bytes
    try:
        audio_bytes = base64.b64decode(agent_res["audio_base64"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to decode base64 audio from TTS Agent: {str(e)}"
        )
        
    # 7. Save audio file
    saved_file_info = storage_service.save_audio_chat_bytes(
        audio_bytes=audio_bytes,
        extension=agent_res["file_extension"],
        prefix="chat_tts"
    )
    
    relative_path = saved_file_info["relative_path"]
    
    # 8. Update DB and commit
    try:
        message.tts_path = relative_path
        message.tts_timestamps = agent_res["timestamps"]
        db.commit()
        db.refresh(message)
    except Exception as e:
        # DB Commit failed - clean up saved file
        db.rollback()
        project_root = storage_service.get_project_root()
        full_path_to_delete = project_root / relative_path
        if os.path.exists(full_path_to_delete):
            try:
                os.remove(full_path_to_delete)
            except Exception as delete_err:
                # Log but do not block raising the original exception
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save TTS audio details to database: {str(e)}"
        )
        
    # Explicitly compute URL from path (do not rely on ORM property serialization)
    computed_url = storage_service.path_to_url(message.tts_path) if message.tts_path else None
    
    return {
        "message_id": message.id,
        "tts_path": message.tts_path,
        "tts_url": computed_url,
        "tts_timestamps": message.tts_timestamps,
        "duration_seconds": agent_res["duration_seconds"],
        "mode": agent_res["mode"]
    }

class TTSSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = "vi_female"
    language: Optional[str] = "vi"
    speed: Optional[float] = 1.0

@router.post("/synthesize")
def synthesize_custom_text(
    payload: TTSSynthesizeRequest,
    db: Session = Depends(get_db)
):
    """
    Synthesize arbitrary Vietnamese/English text using VieNeu TTS agent.
    Saves audio to static abstract storage and returns temporary URL.
    """
    text = payload.text
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty"
        )
        
    sanitized_text = sanitize_text(text)
    if not sanitized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sanitized text is empty. Cannot synthesize speech."
        )
        
    voice_map = {
        "vi_female": "Ngọc Linh",
        "vi_male": "Gia Bảo"
    }
    target_voice = voice_map.get(payload.voice, "Ngọc Linh")
    
    agent_payload = {
        "text": sanitized_text,
        "voice": target_voice,
        "language": payload.language,
        "speed": payload.speed
    }
    
    try:
        agent_res = synthesize_text(agent_payload)
        audio_bytes = base64.b64decode(agent_res["audio_base64"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate or decode audio from TTS Agent: {str(e)}"
        )
        
    saved_file_info = storage_service.save_audio_abstract_bytes(
        audio_bytes=audio_bytes,
        extension=agent_res["file_extension"],
        prefix="custom_tts"
    )
    
    return {
        "audio_url": saved_file_info["url"],
        "duration_seconds": agent_res["duration_seconds"],
        "mode": agent_res["mode"]
    }


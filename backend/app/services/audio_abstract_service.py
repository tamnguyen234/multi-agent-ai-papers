import os
import re
import base64
import logging
import unicodedata
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.paper import Paper
from app.db.models.audio import AudioAbstract
from app.services.tts_client import synthesize_text
from app.services import storage_service

logger = logging.getLogger(__name__)

# Global in-memory set to track ongoing generations to prevent concurrent duplicate TTS calls
active_generations = set()

def sanitize_text(text: str) -> str:
    """
    Sanitize text before sending to TTS:
    - Bỏ prefix '[Dự phòng - Ollama offline]' (case-insensitive)
    - Bỏ markdown table và dòng chứa nhiều ký tự |---|, ||||, ----
    - Bỏ tag <br>
    - Bỏ ký tự điều khiển/lạ, giữ Unicode tiếng Việt
    - Giới hạn khoảng 1200 ký tự
    """
    if not text:
        return ""
    
    # 1. Bỏ prefix
    text = re.sub(r"^\[Dự phòng - Ollama offline\]\s*", "", text, flags=re.IGNORECASE)
    
    # 2. Bỏ markdown tables
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
    
    # 4. Bỏ ký tự điều khiển/lạ, giữ lại Unicode Vietnamese
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\r\n\t")
    
    # 5. Cắt còn 1200 ký tự
    text = text[:1200].strip()
    return text

def generate_audio_for_paper_summary(
    db: Session,
    paper: Paper,
    force: bool = False,
    voice: str = "vi_female",
    language: str = "vi"
) -> dict:
    """
    Generate or update the audio abstract for a given paper.
    If the file exists and force=False, returns the cached metadata with mode="existing".
    If the file is missing/corrupted or force=True:
      - Uses in-memory synchronization lock to prevent concurrent duplicate generation.
      - Calls the TTS agent to synthesize WAV bytes with voice mapping and logging.
      - Commits to the database first, then deletes any old audio files to ensure safety.
      - Cleans up newly generated files if a database error occurs.
    """
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )

    project_root = storage_service.get_project_root()
    
    # Idempotency check: look up existing record
    existing_audio = db.query(AudioAbstract).filter(AudioAbstract.paper_id == paper.id).first()
    
    # If file exists, is valid (>0 bytes), and force=False, always return existing
    if existing_audio and not force:
        file_path_on_disk = project_root / existing_audio.file_path.lstrip("/")
        if os.path.exists(file_path_on_disk) and os.path.getsize(file_path_on_disk) > 0:
            return {
                "paper_id": paper.id,
                "audio_path": existing_audio.file_path,
                "audio_url": existing_audio.audio_url,
                "duration_seconds": existing_audio.duration_seconds,
                "voice": existing_audio.voice,
                "language": existing_audio.language,
                "mode": "existing",
                "audio_abstract": existing_audio
            }

    # Concurrent request protection
    if paper.id in active_generations:
        logger.warning(f"Audio Abstract Generation already in progress for paper ID {paper.id}. Rejecting duplicate request.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Audio abstract generation for this paper is already in progress. Please wait."
        )

    # Register active generation
    active_generations.add(paper.id)
    
    try:
        # Determine the text to read
        raw_text = paper.summary
        if not raw_text or not raw_text.strip():
            raw_text = paper.abstract
            
        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Both summary and abstract are empty for paper ID {paper.id}."
            )
            
        # Sanitize text
        sanitized_text = sanitize_text(raw_text)
        if not sanitized_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sanitized text is empty for paper ID {paper.id}. Cannot synthesize speech."
            )

        # Voice mapping
        voice_map = {
            "vi_female": "Ngọc Linh",
            "vi_male": "Gia Bảo"
        }
        resolved_voice = voice_map.get(voice, "Ngọc Linh")
        
        # Log voice parameters
        logger.info(
            f"Starting TTS generation for paper ID {paper.id}. "
            f"Requested Voice: {voice}, Resolved Voice: {resolved_voice}, Language: {language}"
        )
        
        # Call TTS Agent
        payload = {
            "text": sanitized_text,
            "voice": resolved_voice,
            "language": language,
            "speed": 1.0
        }
        
        agent_res = synthesize_text(payload)
        
        # Decode base64 WAV payload
        try:
            audio_bytes = base64.b64decode(agent_res["audio_base64"], validate=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to decode base64 audio from TTS Agent: {str(e)}"
            )
            
        # Save audio bytes to data/audio_abstract/
        saved_file_info = storage_service.save_audio_abstract_bytes(
            audio_bytes=audio_bytes,
            extension=agent_res["file_extension"],
            prefix="abstract_tts"
        )
        
        relative_path = saved_file_info["relative_path"]
        
        # Track the old file path for safe cleanup ONLY after DB commit succeeds
        old_file_path = None
        
        try:
            # Create or update AudioAbstract database record
            if existing_audio:
                # Track old file path if path is changing
                if existing_audio.file_path != relative_path:
                    old_file_path = project_root / existing_audio.file_path.lstrip("/")
                existing_audio.file_path = relative_path
                existing_audio.duration_seconds = int(agent_res["duration_seconds"])
                existing_audio.paper_timestamps = agent_res["timestamps"]
                existing_audio.voice = resolved_voice # Store actual resolved voice name in DB
                existing_audio.language = language
                db.add(existing_audio)
            else:
                existing_audio = AudioAbstract(
                    paper_id=paper.id,
                    file_path=relative_path,
                    duration_seconds=int(agent_res["duration_seconds"]),
                    paper_timestamps=agent_res["timestamps"],
                    voice=resolved_voice, # Store actual resolved voice name in DB
                    language=language
                )
                db.add(existing_audio)
                
            paper.has_audio = True
            db.commit()
            
            # Retrieve updated model context
            db.refresh(paper)
            db.refresh(existing_audio)
            
            # Safely remove the old file only now that the DB update has succeeded
            if old_file_path and os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as fe:
                    logger.warning(f"Failed to delete old audio abstract file {old_file_path}: {str(fe)}")
                    
            return {
                "paper_id": paper.id,
                "audio_path": existing_audio.file_path,
                "audio_url": existing_audio.audio_url,
                "duration_seconds": existing_audio.duration_seconds,
                "voice": existing_audio.voice,
                "language": existing_audio.language,
                "mode": "generated",
                "audio_abstract": existing_audio
            }
            
        except Exception as db_err:
            db.rollback()
            # Clean up the newly generated file to avoid leaving orphan files on failure
            new_file_to_delete = project_root / relative_path.lstrip("/")
            if os.path.exists(new_file_to_delete):
                try:
                    os.remove(new_file_to_delete)
                except Exception as fe:
                    logger.error(f"Failed to remove newly generated audio file on rollback: {str(fe)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save audio abstract details to database: {str(db_err)}"
            )
            
    finally:
        # Deregister active generation to release lock
        active_generations.discard(paper.id)

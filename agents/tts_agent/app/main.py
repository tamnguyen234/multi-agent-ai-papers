from fastapi import FastAPI, HTTPException, status
import logging
import os
import re
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()

from app.schemas import TTSRequest, TTSResponse
from app.tts_engine import synthesize_text
from app.real_tts import RealTTSEngine

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts_agent")

app = FastAPI(
    title="TTS Agent",
    description="Agent for converting text abstract summaries or QA replies into speech audio files (Text-to-Speech) using VieNeu.",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"message": "TTS Agent is running"}

@app.get("/health")
def health_check():
    """
    Return service health check status.
    Must not trigger model weights load.
    """
    engine = RealTTSEngine.get_instance()
    env_mode = os.getenv("TTS_MODE", "mock_fallback").lower().strip()
    return {
        "status": "ok",
        "service": "tts_agent",
        "mode": env_mode,
        "model_loaded": engine.is_loaded()
    }

@app.post("/tts/synthesize", response_model=TTSResponse)
def text_to_speech_synthesize(payload: TTSRequest):
    """
    Synthesize text into speech audio.
    Includes text validation, length limits, whitespace normalization, and fallback.
    """
    text = payload.text
    
    # 1. Validate text must not be empty
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty"
        )
        
    # 2. Normalize text: strip and collapse multiple whitespaces
    normalized_text = text.strip()
    normalized_text = re.sub(r'\s+', ' ', normalized_text)
    
    # 3. Enforce max length of 2000 characters
    if len(normalized_text) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text length exceeds the maximum limit of 2000 characters"
        )
        
    payload.text = normalized_text

    # 4. Trigger synthesis process
    try:
        result = synthesize_text(payload)
        return TTSResponse(**result)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Synthesis endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {str(e)}"
        )

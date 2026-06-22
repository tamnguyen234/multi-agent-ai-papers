from fastapi import FastAPI, HTTPException, status
import logging
import os
import re
import urllib.request
import urllib.parse
import json
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()

# If running in mock or mock_fallback mode, disable HF hub downloads to prevent API hangs
env_mode = os.getenv("TTS_MODE", "mock_fallback").lower().strip()
if env_mode in ("mock", "mock_fallback"):
    os.environ["HF_HUB_OFFLINE"] = "1"
    logging.info("Offline mode active: HF_HUB_OFFLINE=1 (disabling online model downloads)")

def translate_free_api(text: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": "vi",
        "dt": "t",
        "q": text
    }
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    req = urllib.request.Request(
        full_url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        translated_parts = [item[0] for item in data[0] if item[0]]
        return "".join(translated_parts)

from app.schemas import TTSRequest, TTSResponse, TranslateRequest, TranslateResponse
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
    
    # 3. Enforce max length of 2000 characters by truncating to avoid API failures
    if len(normalized_text) > 2000:
        logger.warning(f"Text length ({len(normalized_text)}) exceeds 2000 limit. Truncating to prevent failure.")
        normalized_text = normalized_text[:2000].rsplit(' ', 1)[0]
        
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

@app.post("/tts/translate", response_model=TranslateResponse)
def translate_text(payload: TranslateRequest):
    """
    Translate English text to Vietnamese.
    """
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty"
        )
    
    env_mode = os.getenv("TTS_MODE", "mock_fallback").lower().strip()
    
    # 1. If in mock mode, try free Google Translate API first, fallback to mock text
    if env_mode == "mock":
        try:
            translated = translate_free_api(payload.text)
            return TranslateResponse(translated_text=translated)
        except Exception:
            return TranslateResponse(translated_text=f"[Bản dịch giả lập] {payload.text}")
    
    # 2. In mock_fallback or real, try local model first
    try:
        engine = RealTTSEngine.get_instance()
        translated = engine.translate_en_to_vi(payload.text)
        return TranslateResponse(translated_text=translated)
    except Exception as e:
        logger.error(f"Local translation failed: {str(e)}. Attempting free Translate API fallback...")
        try:
            # 3. Fallback to free Google Translate API
            translated = translate_free_api(payload.text)
            return TranslateResponse(translated_text=translated)
        except Exception as fe:
            logger.error(f"Free Translate API fallback also failed: {str(fe)}")
            return TranslateResponse(translated_text=f"[Bản dịch giả lập] {payload.text}")



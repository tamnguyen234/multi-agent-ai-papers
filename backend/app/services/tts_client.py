import httpx
import logging
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger("backend_gateway.tts_client")

def synthesize_text(payload: dict) -> dict:
    """
    Call the TTS Agent to synthesize speech.
    Timeout is set to 300 seconds to allow for VieNeu model CPU inference.
    """
    url = f"{settings.TTS_AGENT_URL.rstrip('/')}/tts/synthesize"
    
    # Log the request payload after sanitization
    logger.info(f"Sending synthesis request to TTS Agent at {url}. Payload: {payload}")
    
    try:
        response = httpx.post(url, json=payload, timeout=300.0)
        
        # Log response status code
        logger.info(f"TTS Agent responded with status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"TTS Agent error response body: {response.text}")
            
        response.raise_for_status()
    except httpx.ConnectError as ce:
        logger.exception(f"Connection error to TTS Agent: {str(ce)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not connect to TTS Agent. Please ensure it is running. Reason: {str(ce)}"
        )
    except httpx.TimeoutException as te:
        logger.exception(f"Timeout error calling TTS Agent: {str(te)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Request to TTS Agent timed out after 300 seconds. Reason: {str(te)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error communicating with TTS Agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with TTS Agent: {str(e)}"
        )
        
    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from TTS Agent: Response is not valid JSON."
        )
        
    # Validate required fields
    required_fields = ["audio_base64", "mime_type", "file_extension"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Invalid response format from TTS Agent: missing '{field}' field."
            )
            
    # Validate allowed extensions
    file_ext = data["file_extension"]
    allowed_extensions = [".wav", ".mp3", ".ogg", ".m4a"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Invalid file extension '{file_ext}' returned by TTS Agent. Allowed extensions are: {', '.join(allowed_extensions)}"
        )
        
    return {
        "mode": data.get("mode", "mock"),
        "audio_base64": data["audio_base64"],
        "mime_type": data["mime_type"],
        "file_extension": data["file_extension"],
        "duration_seconds": data.get("duration_seconds", 1.0),
        "timestamps": data.get("timestamps", [])
    }

from typing import Optional

def translate_text(text: str, mode: Optional[str] = None) -> dict:
    """
    Call the TTS Agent to translate English text into Vietnamese.
    """
    url = f"{settings.TTS_AGENT_URL.rstrip('/')}/tts/translate"
    payload = {"text": text}
    if mode:
        payload["mode"] = mode
        
    logger.info(f"Sending translate request to TTS Agent at {url}. Text length: {len(text)}")
    
    try:
        import httpx
        response = httpx.post(url, json=payload, timeout=120.0)
        response.raise_for_status()
    except Exception as e:
        logger.exception(f"Error communicating with TTS Agent for translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with TTS Agent: {str(e)}"
        )
        
    try:
        data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from TTS Agent: Response is not valid JSON."
        )
        
    if "translated_text" not in data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from TTS Agent: missing 'translated_text' field."
        )
        
    return data


import os
import logging
from app.schemas import TTSRequest
from app.mock_tts import synthesize_mock
from app.real_tts import RealTTSEngine
from app.utils_audio import get_wav_duration, convert_to_base64

logger = logging.getLogger("tts_agent")

def synthesize_text(request: TTSRequest) -> dict:
    """
    Synthesize text based on mode configuration.
    Priority: request.mode (if provided) > Environment variable TTS_MODE.
    """
    # 1. Resolve Mode
    env_mode = os.getenv("TTS_MODE", "mock_fallback").lower().strip()
    mode = request.mode.lower().strip() if request.mode else env_mode

    # Validate Mode
    allowed_modes = ["mock", "real", "mock_fallback"]
    if mode not in allowed_modes:
        raise ValueError(f"Invalid mode '{mode}'. Allowed modes are: {', '.join(allowed_modes)}")

    logger.info(f"Synthesize execution starting. Mode: '{mode}'")

    # 2. Execute based on Mode
    if mode == "mock":
        res = synthesize_mock(request.text)
        res["mode"] = "mock"
        res["fallback_reason"] = None
        return res

    elif mode == "real":
        # Raise errors directly if anything fails in real mode
        engine = RealTTSEngine.get_instance()
        wav_bytes = engine.synthesize(
            text=request.text,
            voice=request.voice or "default",
            language=request.language or "vi",
            speed=request.speed or 1.0
        )
        duration = get_wav_duration(wav_bytes)
        audio_b64 = convert_to_base64(wav_bytes)
        return {
            "audio_base64": audio_b64,
            "mime_type": "audio/wav",
            "file_extension": ".wav",
            "duration_seconds": duration,
            "timestamps": None,
            "mode": "real",
            "fallback_reason": None
        }

    else:  # mock_fallback
        try:
            engine = RealTTSEngine.get_instance()
            wav_bytes = engine.synthesize(
                text=request.text,
                voice=request.voice or "default",
                language=request.language or "vi",
                speed=request.speed or 1.0
            )
            duration = get_wav_duration(wav_bytes)
            audio_b64 = convert_to_base64(wav_bytes)
            return {
                "audio_base64": audio_b64,
                "mime_type": "audio/wav",
                "file_extension": ".wav",
                "duration_seconds": duration,
                "timestamps": None,
                "mode": "real",
                "fallback_reason": None
            }
        except Exception as e:
            # Catch loading or generation errors and fallback to mock WAV bytes
            simplified_error = str(e)
            if "VieNeu model load failed" not in simplified_error:
                simplified_error = f"VieNeu model load failed: {e.__class__.__name__}: {simplified_error}"
                
            logger.warning(f"Real TTS failed. Falling back to mock. Reason: {simplified_error}")
            
            res = synthesize_mock(request.text)
            res["mode"] = "mock_fallback"
            res["fallback_reason"] = simplified_error
            return res

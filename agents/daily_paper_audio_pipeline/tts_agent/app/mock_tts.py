import base64
import io
from gtts import gTTS

def synthesize_mock(text: str) -> dict:
    """
    Generate mock translation/TTS using Google TTS (gTTS) instead of simple silence,
    or fallback to 1s silence if gTTS fails.
    """
    try:
        # Generate real speech bytes using gTTS
        tts = gTTS(text=text, lang="vi")
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        mp3_bytes = fp.getvalue()
        
        audio_b64 = base64.b64encode(mp3_bytes).decode('utf-8')
        
        # Estimate duration: ~150 words per minute -> 2.5 words per second (0.4s per word)
        word_count = len(text.split())
        duration = max(1.0, float(word_count) * 0.4)
        
        return {
            "audio_base64": audio_b64,
            "mime_type": "audio/mpeg",
            "file_extension": ".mp3",
            "duration_seconds": duration,
            "timestamps": None
        }
    except Exception as e:
        # Fallback to 1.0 second silence if gTTS request fails
        from app.utils_audio import generate_mock_wav, convert_to_base64
        wav_bytes = generate_mock_wav(duration=1.0)
        audio_b64 = convert_to_base64(wav_bytes)
        return {
            "audio_base64": audio_b64,
            "mime_type": "audio/wav",
            "file_extension": ".wav",
            "duration_seconds": 1.0,
            "timestamps": None
        }


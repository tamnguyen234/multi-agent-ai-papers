from app.utils_audio import generate_mock_wav, convert_to_base64

def synthesize_mock(text: str) -> dict:
    """
    Generate mock silent WAV audio (1.0 second).
    """
    wav_bytes = generate_mock_wav(duration=1.0)
    audio_b64 = convert_to_base64(wav_bytes)
    return {
        "audio_base64": audio_b64,
        "mime_type": "audio/wav",
        "file_extension": ".wav",
        "duration_seconds": 1.0,
        "timestamps": None
    }

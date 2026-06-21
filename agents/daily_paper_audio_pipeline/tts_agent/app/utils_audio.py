import io
import wave
import base64

def generate_mock_wav(duration: float = 1.0, sample_rate: int = 8000) -> bytes:
    """
    Generate 1 second of silent mono 16-bit PCM WAV.
    """
    out_buf = io.BytesIO()
    with wave.open(out_buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # PCM 16-bit = 2 bytes per sample
        num_samples = int(duration * sample_rate)
        wav_file.writeframes(b'\x00' * (num_samples * 2))
    return out_buf.getvalue()

def get_wav_duration(wav_bytes: bytes) -> float:
    """
    Read duration from WAV file bytes.
    """
    try:
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            if rate > 0:
                return round(frames / float(rate), 2)
    except Exception:
        pass
    return 1.0

def convert_to_base64(data: bytes) -> str:
    """
    Convert raw bytes to base64 string.
    """
    return base64.b64encode(data).decode('utf-8')

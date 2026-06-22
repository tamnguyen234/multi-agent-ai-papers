import httpx

from app.config import PipelineSettings, get_settings
from app.schemas import TTSResult



class TTSClient:
    def __init__(self, settings: PipelineSettings | None = None):
        self.settings = settings or get_settings()

    def synthesize_vi(
        self,
        text: str,
        voice: str = "default",
        language: str = "vi",
        speed: float = 1.0,
        mode: str | None = None,
    ) -> TTSResult:
        payload: dict[str, object] = {
            "text": text,
            "voice": voice,
            "language": language,
            "speed": speed,
        }
        if mode:
            payload["mode"] = mode

        url = f"{self.settings.tts_agent_url.rstrip('/')}/tts/synthesize"
        response = httpx.post(url, json=payload, timeout=self.settings.tts_timeout_seconds)
        response.raise_for_status()
        data = response.json()
        for field in ("audio_base64", "mime_type", "file_extension"):
            if field not in data:
                raise ValueError(f"TTS agent response missing '{field}'.")
        return TTSResult(**data)


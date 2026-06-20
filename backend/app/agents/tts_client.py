import httpx
from app.core.config import settings

class TTSClient:
    def __init__(self):
        self.base_url = settings.TTS_AGENT_URL

    async def text_to_speech(self, text: str, output_path: str):
        """Send text to TTS Agent and save the synthesized speech output."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/tts",
                    json={"text": text, "output_path": output_path},
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"status": "error", "message": str(exc)}

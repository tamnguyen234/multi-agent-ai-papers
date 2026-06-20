import httpx
from app.core.config import settings

class SummarizerClient:
    def __init__(self):
        self.base_url = settings.SUMMARIZER_AGENT_URL

    async def fetch_and_summarize(self, count: int = 5):
        """Call Summarizer Agent to fetch top AI papers and summarize them."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/summarize", json={"count": count}, timeout=60.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                # Handle error appropriately (logging etc.)
                return {"status": "error", "message": str(exc)}

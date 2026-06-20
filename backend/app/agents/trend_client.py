import httpx
from app.core.config import settings

class TrendClient:
    def __init__(self):
        self.base_url = settings.TREND_AGENT_URL

    async def analyze_topics(self, paper_ids: list[int]):
        """Call Trend Agent to cluster topics from paper abstracts."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/analyze", json={"paper_ids": paper_ids}, timeout=60.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"status": "error", "message": str(exc)}

import httpx
from app.core.config import settings

class QAClient:
    def __init__(self):
        self.base_url = settings.QA_AGENT_URL

    async def initialize_index(self, paper_id: int, pdf_path: str):
        """Send PDF to Q&A Agent to build its FAISS vector index."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/index",
                    json={"paper_id": paper_id, "pdf_path": pdf_path},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"status": "error", "message": str(exc)}

    async def query_paper(self, paper_id: int, question: str):
        """Ask a question about a specific indexed paper."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/query",
                    json={"paper_id": paper_id, "question": question},
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                return {"status": "error", "message": str(exc)}

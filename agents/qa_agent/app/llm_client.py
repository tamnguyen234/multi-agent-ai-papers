import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

def generate_llm_answer(question: str, context_chunks: list) -> str:
    """
    Send query with context to Ollama local LLM.
    """
    if settings.QA_LLM_PROVIDER.lower() != "ollama":
        raise ValueError(f"Unsupported LLM provider: {settings.QA_LLM_PROVIDER}")
        
    # Construct context text
    context_text = "\n\n".join([
        f"[Trang {c['page']}]: {c['text']}"
        for c in context_chunks
    ])
    
    prompt = f"""Bạn là một trợ lý nghiên cứu khoa học chuyên nghiệp. Hãy trả lời câu hỏi của người dùng dựa TRÊN thông tin trích dẫn từ bài báo được cung cấp dưới đây.

YÊU CẦU:
1. Chỉ trả lời dựa trên phần thông tin trích dẫn được cung cấp (Context).
2. Nếu trong phần trích dẫn không có thông tin để trả lời câu hỏi, hãy nêu rõ "Tôi không tìm thấy thông tin này trong bài báo." và không tự bịa câu trả lời.
3. Không tự bịa số trang hoặc trích dẫn không có trong Context.
4. Trả lời bằng ngôn ngữ tương ứng với câu hỏi (Tiếng Việt nếu hỏi bằng Tiếng Việt, Tiếng Anh nếu hỏi bằng Tiếng Anh).

---
THÔNG TIN TRÍCH DẪN (CONTEXT):
{context_text}

---
CÂU HỎI:
{question}

---
TRẢ LỜI:"""

    url = f"{settings.QA_OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.QA_OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = httpx.post(url, json=payload, timeout=120.0)  # 120s for heavy LLM inference
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except httpx.HTTPError as he:
        raise ValueError(f"Ollama server returned error: {str(he)}")
    except Exception as e:
        raise ValueError(f"Failed to communicate with Ollama: {str(e)}")

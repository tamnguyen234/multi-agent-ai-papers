from __future__ import annotations
import httpx
import logging
import re
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên phân tích tài liệu PDF học thuật.

## Nguyên tắc bắt buộc
1. CHỈ trả lời dựa trên nội dung tài liệu được cung cấp bên dưới. Nếu tài liệu không chứa thông tin liên quan, hãy nói rõ: "Tài liệu không đề cập đến vấn đề này."
2. Trả lời bằng tiếng Việt. Giữ nguyên các thuật ngữ kỹ thuật tiếng Anh gốc (ví dụ: Transformer, Attention, Loss function).
3. TUYỆT ĐỐI KHÔNG sử dụng tiếng Trung (Chinese) trong bất kỳ trường hợp nào.
4. KHÔNG sử dụng ký hiệu Toán học hoặc LaTeX.
5. Trả lời ngắn gọn, nhưng chi tiết về nội dung, đảm bảo đầy đủ mọi thông tin.
6. Định dạng bằng Markdown (in đậm, danh sách, tiêu đề nhỏ)."""

USER_PROMPT_TEMPLATE = """Dưới đây là nội dung trích xuất từ tài liệu PDF:

{context}
{memory}
Câu hỏi: {question}"""

def _format_memory(history: list[dict[str, Any]] | None) -> str:
    if not history:
        return ""

    memory_text = "\n[Lịch sử hỏi đáp gần đây trong phiên]\n"
    for item in history:
        question = item.get("q") or item.get("question") or ""
        answer = item.get("a") or item.get("answer") or ""
        if question or answer:
            memory_text += f"Người dùng: {question}\nTrả lời: {answer}\n\n"
    return memory_text

def _strip_thinking(raw: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    if not cleaned and "</think>" in raw:
        cleaned = raw.split("</think>")[-1].strip()
    return cleaned

def generate_llm_answer(question: str, context_chunks: list, history: list[dict[str, Any]] | None = None) -> str:
    """
    Send query with context to Ollama local LLM using Agent2-style /api/chat.
    """
    if settings.QA_LLM_PROVIDER.lower() != "ollama":
        raise ValueError(f"Unsupported LLM provider: {settings.QA_LLM_PROVIDER}")
        
    # Construct context text
    context_text = "\n\n".join([
        f"[Trang {c['page']}]: {c['text']}"
        for c in context_chunks
    ])
    context_text = context_text[:settings.QA_CONTEXT_MAX_CHARS]
    memory_text = _format_memory(history)
    
    user_content = USER_PROMPT_TEMPLATE.format(
        context=context_text,
        memory=memory_text,
        question=question,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    
    url = f"{settings.QA_OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {
        "model": settings.QA_OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {
            "num_ctx": settings.QA_OLLAMA_NUM_CTX,
            "num_predict": settings.QA_OLLAMA_NUM_PREDICT,
            "temperature": settings.QA_OLLAMA_TEMPERATURE,
        },
    }
    
    response = httpx.post(url, json=payload, timeout=settings.QA_OLLAMA_TIMEOUT_SECONDS)
    response.raise_for_status()
    data = response.json()
    raw = data.get("message", {}).get("content", "")
    return _strip_thinking(raw)

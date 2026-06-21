def generate_mock_answer(question: str, title: str | None, summary: str | None, abstract: str | None) -> str:
    paper_title = title or "Unknown Title"
    focus = ""
    if summary:
        focus = f" tóm tắt là '{summary[:150]}...'"
    elif abstract:
        focus = f" tóm tắt là '{abstract[:150]}...'"
        
    return (
        f"Dựa trên thông tin hiện có, bài báo '{paper_title}'{focus} tập trung vào nghiên cứu và giải quyết các vấn đề liên quan. "
        f"Câu hỏi của bạn là: '{question}'. Vì đang ở mock mode, đây là câu trả lời mẫu; ở các task sau có thể thay bằng RAG đọc PDF thật."
    )

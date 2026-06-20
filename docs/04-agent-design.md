# 04. Thiết kế các AI Agents (Agent Design)

Mô tả chi tiết kiến trúc bên trong và cơ chế hoạt động của từng Agent chuyên biệt trong hệ thống.

---

## 1. Summarizer Agent (Tác tử thu thập & tóm tắt)
- **Mục tiêu**: Quét nguồn dữ liệu arXiv RSS hàng ngày, chọn lọc bài báo AI tiêu biểu và sinh tóm tắt học thuật chất lượng cao.
- **Công nghệ**:
  - `feedparser` để đọc RSS Feed từ arXiv.
  - Sử dụng mô hình `BART-large-CNN` hoặc `T5` thông qua thư viện `transformers` của Hugging Face để sinh tóm tắt (Abstractive Summarization).
- **Đầu vào**: Tần suất cào (Daily), Từ khóa lọc (`AI`, `Computer Vision`, `Natural Language Processing`, `Multi-Agent`).
- **Đầu ra**: Tiêu đề, danh sách tác giả, tóm tắt gốc, tóm tắt thu gọn dạng markdown.

---

## 2. Trend Agent (Tác tử phân tích xu hướng)
- **Mục tiêu**: Cluster các bài báo đã tải để tìm ra xu hướng chủ đề công nghệ nổi bật trong tuần/tháng.
- **Công nghệ**:
  - `Sentence Transformers` để tạo embedding cho abstracts bài báo.
  - `UMAP` để giảm số chiều vector.
  - `HDBSCAN` để phân cụm mật độ.
  - `BERTopic` để sinh nhãn chủ đề tự động cho từng cụm (Topic Modeling).
- **Đầu vào**: Tập hợp các abstracts của bài báo lưu trong DB.
- **Đầu ra**: Biểu đồ phân cụm chủ đề, tỷ lệ phần trăm phân bố chủ đề nóng theo thời gian.

---

## 3. Q&A Agent (Tác tử hỏi đáp RAG)
- **Mục tiêu**: Trả lời các câu hỏi chuyên sâu của người dùng về nội dung cụ thể trong file PDF bài báo.
- **Công nghệ**:
  - `pymupdf4llm` trích xuất văn bản từ file PDF giữ nguyên cấu trúc Markdown.
  - `LangChain` quản lý chu trình RAG (Retrieval-Augmented Generation).
  - `FAISS` lưu trữ vector database cục bộ của từng bài báo.
  - Kết nối mô hình LLM cục bộ qua `Ollama` (ví dụ model `llama3` hoặc `mistral`).
- **Đầu vào**: ID bài báo + Câu hỏi của người dùng.
- **Đầu ra**: Phản hồi bằng chữ kèm theo các đoạn trích dẫn nguồn từ tài liệu gốc.

---

## 4. TTS Agent (Tác tử chuyển đổi giọng nói)
- **Mục tiêu**: Chuyển đổi tóm tắt bài báo và nội dung phản hồi chat thành file âm thanh chất lượng tốt.
- **Công nghệ**:
  - Thư viện `transformers` chạy các mô hình TTS như Bark hoặc VITS.
  - Thư viện tiếng Việt `vieneu` hoặc các giải pháp TTS tiếng Việt chuyên biệt giúp phát âm tự nhiên.
- **Đầu vào**: Chuỗi văn bản thuần (Text).
- **Đầu ra**: File âm thanh định dạng `.wav` hoặc `.mp3` lưu tại thư mục `./data/audio_abstract/` hoặc `./data/audio_chat_message/`.

# Q&A Agent (RAG)

Agent này chịu trách nhiệm hỗ trợ hỏi đáp trên nội dung chi tiết của các bài báo khoa học PDF thông qua mô hình RAG (Retrieval-Augmented Generation).

---

## 🛠️ Luồng hoạt động chính
1. **Trích xuất & Cắt mảnh (Chunking)**: Sử dụng `PyMuPDF` và `pymupdf4llm` để đọc file PDF bài báo và chia nhỏ văn bản thành các mảnh.
2. **Nhúng Vector (Embedding)**: Chuyển đổi các mảnh văn bản thành vector embeddings bằng Ollama `nomic-embed-text`.
3. **Lưu trữ Vector Database (Lớp cơ sở)**: Lưu trữ các vector biểu diễn vào cơ sở dữ liệu vector cục bộ `FAISS` trong thư mục `data/indices_v2/`.
4. **Hỏi đáp RAG**: Khi có câu hỏi, lấy 6 mảnh ứng viên từ FAISS, rerank bằng `BAAI/bge-reranker-base`, chọn 3 mảnh tốt nhất, đưa tối đa 5000 ký tự context và 3 lượt history gần nhất vào prompt rồi gọi Ollama `/api/chat`.

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định: `8103` (URL: `http://localhost:8103`)

---

## 🚀 Hướng dẫn khởi chạy

### 1. Cài đặt thư viện
```bash
cd agents/qa_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Cấu hình `.env`
Sao chép `.env.example` thành `.env` và cập nhật cấu hình:
```bash
cp .env.example .env
```
*Lưu ý:* Cài đặt Ollama và tải model trước khi chạy dịch vụ này:
```bash
ollama pull qwen3.5:4b
ollama pull nomic-embed-text
```

### 3. Chạy Agent
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8103
```

---

## 🔌 Endpoints chính
- `GET /health`: Kiểm tra trạng thái hoạt động.
- `POST /index`: Nạp tài liệu PDF và khởi tạo Vector Database FAISS.
- `POST /query`: Đặt câu hỏi truy vấn nội dung tài liệu.
- `POST /qa/ask`: Endpoint Q&A thật được Backend Gateway sử dụng.

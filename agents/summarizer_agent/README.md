# Summarizer Agent

Agent này chịu trách nhiệm tự động quét và lấy các bài báo AI mới nhất từ **arXiv RSS feed**, chọn ra các bài báo nổi bật và sinh tóm tắt nội dung học thuật bằng các mô hình ngôn ngữ lớn (LLMs).

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định: `8101` (URL: `http://localhost:8101`)

---

## 🚀 Hướng dẫn khởi chạy

### 1. Cài đặt thư viện
```bash
cd agents/summarizer_agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Cấu hình `.env`
Sao chép `.env.example` thành `.env` và cập nhật cấu hình:
```bash
cp .env.example .env
```

### 3. Chạy Agent
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8101
```

---

## 🔌 Endpoints chính
- `GET /health`: Kiểm tra trạng thái hoạt động.
- `POST /summarize`: Bắt đầu lấy tin và tóm tắt bài báo.

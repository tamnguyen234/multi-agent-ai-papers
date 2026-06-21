# TTS Agent (Text-To-Speech)

Agent này chịu trách nhiệm chuyển đổi tóm tắt bài báo AI dạng văn bản (text) hoặc các câu trả lời tương tác thành các file âm thanh (audio) bằng tiếng Việt hoặc tiếng Anh để lưu cục bộ trong hệ thống.

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định: `8104` (URL: `http://localhost:8104`)

---

## 🚀 Hướng dẫn khởi chạy

### 1. Cài đặt thư viện
```bash
cd agents/tts_agent
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
uvicorn app.main:app --reload --host 127.0.0.1 --port 8104
```

---

## 🔌 Endpoints chính
- `GET /health`: Kiểm tra trạng thái hoạt động.
- `POST /tts`: Sinh audio từ văn bản đầu vào.

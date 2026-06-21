# Trend Agent

Agent này chịu trách nhiệm phân tích xu hướng chủ đề (Topic Modeling) từ các tóm tắt bài báo AI đã lưu trữ trong cơ sở dữ liệu. Nó gom cụm các bài viết bằng thuật toán BERTopic để xác định những chủ đề công nghệ AI đang "nóng".

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định: `8102` (URL: `http://localhost:8102`)

---

## 🚀 Hướng dẫn khởi chạy

### 1. Cài đặt thư viện
```bash
cd agents/trend_agent
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
uvicorn app.main:app --reload --host 127.0.0.1 --port 8102
```

---

## 🔌 Endpoints chính
- `GET /health`: Kiểm tra trạng thái hoạt động.
- `POST /analyze`: Phân tích gom cụm các bài báo được chỉ định.

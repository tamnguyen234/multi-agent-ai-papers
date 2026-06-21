# 02. Kiến trúc hệ thống (System Architecture)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20

---

## 1. Tổng quan kiến trúc

Hệ thống **AI Paper Multi-Agent System** được thiết kế theo mô hình **API Gateway + Microservices**. Backend FastAPI đóng vai trò trung tâm điều phối (Orchestrator), xác thực người dùng và lập lịch tác vụ. Bốn Agent AI chạy độc lập dưới dạng microservice FastAPI riêng biệt, giao tiếp qua HTTP REST.

**Nguyên tắc thiết kế:**
- Frontend **không** gọi trực tiếp Agent – chỉ gọi Backend Gateway.
- Database **chỉ** lưu metadata và đường dẫn file (không lưu nội dung nhị phân).
- File PDF, Audio, FAISS Index nằm trong thư mục `data/` cục bộ – không commit lên Git.
- Mỗi Agent chạy độc lập và có thể scale riêng.

---

## 2. Sơ đồ kiến trúc tổng thể

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                        │
│                                                                             │
│     Browser (http://localhost:5173)                                         │
│     React + Vite + TypeScript SPA                                           │
│     - AuthContext / ToastContext / UserContext                               │
│     - Pages: Papers, Paper Detail, Chat, Trend, Profile, Login/Register     │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │ REST API (JWT Bearer)
                          │ VITE_API_BASE_URL=http://127.0.0.1:8000
                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                      BACKEND GATEWAY (Port 8000)                           │
│                        FastAPI + SQLAlchemy                                 │
│                                                                             │
│   Modules:                                                                  │
│   ├── app/api/v1/          → API Routers (auth, papers, chat, trend, ...)   │
│   ├── app/services/        → Business Logic + Agent HTTP Clients            │
│   ├── app/repositories/    → Database Access Layer (SQLAlchemy ORM)         │
│   ├── app/schemas/         → Pydantic request/response models               │
│   ├── app/core/            → Config, JWT security, dependencies             │
│   ├── app/db/              → SQLAlchemy engine, Base, migrations (Alembic)  │
│   └── app/jobs/            → APScheduler daily digest job (02:00 AM)       │
└────────┬───────────────────────────────────────────┬───────────────────────┘
          │ SQLAlchemy ORM                             │ HTTP (httpx / requests)
          ▼                                           ▼
┌──────────────────┐          ┌────────────────────────────────────────────┐
│  MySQL Database  │          │           AI Agent Services                 │
│  (ai_papers)     │          │                                             │
│  Port: 3306      │          │  ┌──────────────────────────────────────┐  │
│                  │          │  │ Summarizer Agent    Port 8101         │  │
│  10 Tables:      │          │  │ feedparser + transformers (BART/T5)  │  │
│  - users         │          │  │ arXiv RSS scraping + summarization   │  │
│  - papers        │          │  └──────────────────────────────────────┘  │
│  - digests       │          │  ┌──────────────────────────────────────┐  │
│  - digest_papers │          │  │ Trend Agent         Port 8102         │  │
│  - audio_abst..  │          │  │ BERTopic + UMAP + HDBSCAN            │  │
│  - chat_sessions │          │  │ sentence-transformers embeddings     │  │
│  - chat_messages │          │  └──────────────────────────────────────┘  │
│  - topics        │          │  ┌──────────────────────────────────────┐  │
│  - paper_topics  │          │  │ Q&A Agent           Port 8103         │  │
│  - notifications │          │  │ LangChain RAG + FAISS + pymupdf4llm │  │
└──────────────────┘          │  │ Ollama (qwen3.5 + nomic embeddings) │  │
                              │  └──────────────────────────────────────┘  │
┌──────────────────┐          │  ┌──────────────────────────────────────┐  │
│  Local Storage   │          │  │ TTS Agent           Port 8104         │  │
│  ./data/         │          │  │ transformers (Bark/VITS/SpeechT5)   │  │
│  ├── paper_pdf/  │          │  │ Text → .wav audio file               │  │
│  ├── audio_abs./ │          │  └──────────────────────────────────────┘  │
│  ├── audio_chat/ │          └────────────────────────────────────────────┘
│  ├── faiss_idx/  │
│  └── logs/       │
└──────────────────┘
```

---

## 3. Mô tả chi tiết từng thành phần

### 3.1 Frontend (React + Vite + TypeScript)

| Thuộc tính | Giá trị |
|---|---|
| Framework | React 18 + Vite 5 + TypeScript |
| URL mặc định | http://localhost:5173 |
| Biến môi trường chính | `VITE_API_BASE_URL=http://127.0.0.1:8000` |
| Auth | JWT Bearer Token, lưu trong `localStorage` |
| State Management | React Context (`AuthContext`, `UserContext`, `ToastContext`) |
| HTTP Client | `axios` instance tập trung tại `src/api/client.ts` |

**Các trang chính:**
- `/login`, `/register` – Đăng nhập, đăng ký
- `/papers` – Danh sách bài báo AI
- `/papers/:id` – Chi tiết bài báo + PDF viewer + Audio player
- `/papers/:id/chat` – Chat hỏi đáp RAG
- `/trend` – Dashboard xu hướng chủ đề
- `/profile` – Cài đặt tài khoản + toggle thông báo

### 3.2 Backend Gateway (FastAPI)

| Thuộc tính | Giá trị |
|---|---|
| Framework | FastAPI + Uvicorn |
| Port | 8000 |
| ORM | SQLAlchemy 2.x async |
| Auth | OAuth2 Password + JWT (python-jose) |
| Scheduler | APScheduler (daily 02:00 AM) |
| HTTP Client sang Agent | `httpx` async + timeout 120s (Summarizer), 60s (khác) |
| Migration | Alembic |

**Route groups:**
- `/api/v1/auth` – Đăng nhập, đăng ký
- `/api/v1/papers` – CRUD bài báo
- `/api/v1/chat` – Chat sessions + messages
- `/api/v1/trend` – Topic trends
- `/api/v1/tts` – Text-to-Speech
- `/api/v1/digest` – Daily digest
- `/api/v1/users` – Profile, notification settings
- `/api/v1/system` – Health check, DB health
- `/api/v1/dev` – Development utilities (seed, reset, mock data)

### 3.3 AI Agents

| Agent | Port | Mode chính | Fallback |
|---|---|---|---|
| Summarizer Agent | 8101 | `real` (arXiv RSS + BART/T5) | `mock_fallback` |
| Trend Agent | 8102 | `real` (BERTopic) | `rule_based_fallback` |
| Q&A Agent | 8103 | `real` (LangChain + Ollama) | `mock_fallback` |
| TTS Agent | 8104 | `real` (SpeechT5/Bark) | `mock_fallback` |

*Ghi chú: Cập nhật tài liệu này chỉ tham chiếu các file markdown hợp lệ, các liên kết cũ [docs/api_endpoints.md](api_endpoints.md) được quy sang [docs/05-api-design.md](05-api-design.md).*

Mỗi Agent có endpoint `/health` và `/` (root info).  
Backend đọc mode từ biến môi trường (`SUMMARIZER_MODE`, `TREND_MODE`, v.v.).

### 3.4 Database (MySQL)

- Tên database: `ai_papers`
- Port mặc định: `3306`
- 11 bảng, quản lý qua Alembic migration
- Kết nối: `mysql+pymysql://USER:PASSWORD@localhost:3306/ai_papers`
- Docker: `docker compose up -d db` khởi tạo nhanh

### 3.5 Local File Storage (`./data/`)

| Thư mục | Nội dung | Không commit |
|---|---|---|
| `data/paper_pdf/` | PDF bài báo tải từ arXiv | ✅ |
| `data/audio_abstract/` | Audio tóm tắt bài báo | ✅ |
| `data/audio_chat_message/` | Audio phản hồi chat | ✅ |
| `data/indices_v2/` | FAISS vector index per paper | ✅ |
| `data/logs/` | Log file hệ thống | ✅ |

---

## 4. Luồng dữ liệu chính (Data Flows)

### 4.1 Daily Digest (Scheduler)

```
APScheduler (02:00 AM)
  → Summarizer Agent: fetch top papers from arXiv RSS + summarize
  → Backend: lưu papers vào DB + tạo digest
  → TTS Agent: sinh audio cho mỗi paper
  → Backend: cập nhật has_audio=True, lưu audio path
  → Email Service: gửi thông báo cho users có noti_daily=True
```

### 4.2 RAG Chat Flow

```
User gửi câu hỏi (Frontend)
  → Backend: xác thực JWT, tạo/lấy chat_session
  → Q&A Agent: kiểm tra FAISS index
    → Nếu chưa có: đọc PDF → chunk → embed → lưu FAISS index
    → Truy vấn vector → lấy context → gọi LLM → trả lời
  → Backend: lưu chat_messages (user + assistant)
  → TTS Agent: sinh audio cho assistant message (nếu bật)
  → Frontend: hiển thị reply + audio player
```

### 4.3 Trend Analysis Flow

```
User xem trang Trend (Frontend)
  → Backend: GET /api/v1/trend
    → Nếu DB có trend data: trả về luôn
    → Nếu chưa: gọi Trend Agent với abstracts từ DB
      → Trend Agent: embed → UMAP → HDBSCAN/BERTopic → trả topics
  → Backend: lưu topics + paper_topics vào DB
  → Frontend: render biểu đồ + danh sách topic cards
```

---

## 5. Giao tiếp giữa các thành phần

```
Frontend  ←──(CORS: localhost:5173)──→  Backend Gateway
Backend   ←──(HTTP: 127.0.0.1:810x)──→  Agent Services
Backend   ←──(SQLAlchemy ORM)───────→  MySQL Database
Backend   ←──(File I/O)─────────────→  ./data/ (PDF, Audio, FAISS)
```

**CORS:** Backend cho phép origin `http://localhost:5173` (cấu hình trong `app/main.py`).

---

## 6. Môi trường chạy

| Thành phần | Lệnh khởi chạy |
|---|---|
| Backend | `cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| Summarizer Agent | `cd agents/summarizer_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8101` |
| Trend Agent | `cd agents/trend_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8102` |
| Q&A Agent | `cd agents/qa_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8103` |
| TTS Agent | `cd agents/tts_agent && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8104` |
| Frontend | `cd frontend && npm run dev` |

Hoặc dùng script: `scripts\run_all.bat` để mở tất cả song song.

---

*Tham khảo thêm: [docs/03-database-design.md](03-database-design.md) | [docs/05-api-design.md](05-api-design.md) | [docs/04-agent-design.md](04-agent-design.md)*

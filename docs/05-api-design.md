# 05. Thiết kế giao diện API (API Design)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20  
> **Base URL**: `http://127.0.0.1:8000/api/v1`  
> **Auth**: JWT Bearer Token (`Authorization: Bearer <token>`)  
> **Interactive docs**: `http://127.0.0.1:8000/docs` (Swagger UI)

---

## Nhóm API

| Prefix | Tag | Mô tả |
|---|---|---|
| `/auth` | Authentication | Đăng ký, đăng nhập, lấy thông tin user hiện tại |
| `/users` | User Settings | Cài đặt profile, notification |
| `/papers` | AI Papers | Danh sách và chi tiết bài báo |
| `/digests` | Daily Digest | Bản tin hàng ngày |
| `/trend` | Trend Analysis | Phân tích xu hướng chủ đề |
| `/chat` | Paper Chat (RAG) | Hỏi đáp với bài báo |
| `/tts` | Text-to-Speech | Chuyển đổi giọng nói |
| `/system` | System Diagnostics | Health check |
| `/dev` | Development | Seed data, debug (chỉ dùng trong dev) |

---

## 1. Authentication `/auth`

### `POST /auth/register`

Đăng ký tài khoản mới.

**Request Body (JSON):**
```json
{
  "username": "nguyen_van_a",
  "email": "nva@example.com",
  "password": "strongpassword123",
  "full_name": "Nguyễn Văn A"
}
```

**Response 201:**
```json
{
  "id": 1,
  "username": "nguyen_van_a",
  "email": "nva@example.com",
  "full_name": "Nguyễn Văn A",
  "noti_daily": true,
  "created_at": "2026-06-20T10:00:00"
}
```

**Lỗi thường gặp:**
- `400` – Username hoặc email đã tồn tại

---

### `POST /auth/login`

Đăng nhập lấy JWT token.

**Request Body (JSON):**
```json
{
  "username": "nguyen_van_a",
  "password": "strongpassword123"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "nguyen_van_a",
    "email": "nva@example.com",
    "noti_daily": true
  }
}
```

**Lỗi thường gặp:**
- `401` – Sai username hoặc password

---

### `GET /auth/me` 🔒

Lấy thông tin user đang đăng nhập.

**Headers:** `Authorization: Bearer <token>`

**Response 200:** Tương tự UserResponse ở trên.

---

## 2. User Settings `/users`

### `PATCH /users/me/notification` 🔒

Cập nhật cài đặt nhận thông báo digest hàng ngày.

**Request Body (JSON):**
```json
{
  "noti_daily": false
}
```

**Response 200:** UserResponse với `noti_daily` đã cập nhật.

---

## 3. AI Papers `/papers`

### `GET /papers/`

Lấy danh sách bài báo, có hỗ trợ phân trang và tìm kiếm.

**Query Parameters:**

| Param | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `skip` | int | 0 | Offset |
| `limit` | int | 20 | Số bản ghi tối đa |
| `search` | string | — | Tìm trong title và abstract |

**Response 200:**
```json
[
  {
    "id": 1,
    "arxiv_id": "2312.01234",
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models...",
    "summary": "### Key Findings\n- Introduced Transformer...",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "published": "2017-06-12",
    "pdf_path": "data/paper_pdf/2312.01234.pdf",
    "score": 0.92,
    "has_audio": true,
    "created_at": "2026-06-15T02:00:00"
  }
]
```

---

### `GET /papers/{paper_id}`

Lấy chi tiết một bài báo.

**Path Parameters:** `paper_id` (int)

**Response 200:** Tương tự PaperResponse đầy đủ.

**Lỗi thường gặp:**
- `404` – Không tìm thấy bài báo

---

## 4. Daily Digest `/digests`

### `GET /digests/today`

Lấy digest hôm nay (top 5 bài báo theo rank).

**Response 200:**
```json
{
  "id": 10,
  "digest_date": "2026-06-20",
  "papers": [
    {
      "rank_position": 1,
      "paper": { "id": 5, "title": "...", "arxiv_id": "..." }
    }
  ]
}
```

**Lỗi thường gặp:**
- `404` – Chưa có digest hôm nay

---

### `GET /digests/{digest_id}`

Lấy digest theo ID.

---

### `POST /digests/trigger`

Kích hoạt thủ công daily digest job.

**Response 200:**
```json
{"message": "Daily digest job started"}
```

---

## 5. Trend Analysis `/trend`

### `GET /trend/`

Lấy dữ liệu trend đã được tính từ DB (không gọi Trend Agent).

**Query Parameters:**

| Param | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `limit_topics` | int | 20 | Số topic tối đa |
| `limit_papers_per_topic` | int | 10 | Số paper mỗi topic |

**Response 200:**
```json
{
  "mode": "rule_based_fallback",
  "total_papers": 47,
  "topic_count": 8,
  "topics": [
    {
      "id": 1,
      "name": "Large Language Models",
      "description": "...",
      "keywords": ["llm", "gpt", "transformer"],
      "paper_count": 15,
      "confidence_avg": 0.88,
      "papers": [...]
    }
  ]
}
```

---

### `POST /trend/analyze`

Kích hoạt Trend Agent phân tích và lưu topics vào DB.

**Query Parameters:** `limit` (int, optional) – giới hạn số paper đưa vào phân tích.

---

### `GET /trend/health`

Kiểm tra kết nối với Trend Agent microservice.

**Response 200:**
```json
{
  "status": "ok",
  "agent": {"status": "ok", "mode": "rule_based_fallback"}
}
```

---

## 6. Paper Chat (RAG) `/chat`

### `POST /chat/sessions` 🔒

Tạo mới (hoặc lấy lại) phiên chat với một bài báo.

**Request Body (JSON):**
```json
{
  "paper_id": 5
}
```

**Response 201:**
```json
{
  "id": 3,
  "user_id": 1,
  "paper_id": 5,
  "created_at": "2026-06-20T10:05:00"
}
```

---

### `GET /chat/papers/{paper_id}/session` 🔒

Lấy phiên chat hiện tại của user với bài báo.

**Lỗi thường gặp:**
- `404` – Chưa có phiên chat

---

### `POST /chat/messages` 🔒

Gửi câu hỏi vào phiên chat, nhận câu trả lời từ Q&A Agent.

**Request Body (JSON):**
```json
{
  "session_id": 3,
  "question": "Cơ chế Self-Attention hoạt động như thế nào?"
}
```

**Response 200:**
```json
{
  "session": { "id": 3, "paper_id": 5 },
  "user_message": { "id": 10, "role": "user", "content": "..." },
  "assistant_message": { "id": 11, "role": "assistant", "content": "Self-attention cho phép..." },
  "qa_mode": "mock_fallback",
  "sources": ["Trang 3 – Section 3.2 Scaled Dot-Product Attention"]
}
```

---

### `GET /chat/sessions/{session_id}/messages` 🔒

Lấy lịch sử hội thoại của một phiên chat theo thứ tự thời gian.

---

## 7. Text-to-Speech `/tts`

### `POST /tts/chat-message` 🔒

Sinh audio cho một tin nhắn assistant (nếu chưa có).

**Request Body (JSON):**
```json
{
  "message_id": 11,
  "voice": "vi_female",
  "language": "vi",
  "speed": 1.0
}
```

**Response 200:**
```json
{
  "message_id": 11,
  "tts_path": "data/audio_chat_message/chat_tts_20260620_105200.wav",
  "tts_url": "/static/data/audio_chat_message/chat_tts_20260620_105200.wav",
  "tts_timestamps": [],
  "duration_seconds": 4.2,
  "mode": "mock_fallback"
}
```

**Lỗi thường gặp:**
- `400` – Chỉ sinh TTS cho `role=assistant`
- `403` – Không có quyền
- `404` – Không tìm thấy message

---

## 8. System Diagnostics `/system`

### `GET /system/health`

Kiểm tra trạng thái Backend Gateway.

**Response 200:**
```json
{"status": "ok"}
```

---

### `GET /system/db-health`

Kiểm tra kết nối Database.

**Response 200:**
```json
{"status": "ok", "database": "connected"}
```

---

## 9. Static Files

Backend serve file tĩnh từ thư mục `data/`:

| URL Pattern | Thư mục thực |
|---|---|
| `/static/data/paper_pdf/...` | `data/paper_pdf/` |
| `/static/data/audio_abstract/...` | `data/audio_abstract/` |
| `/static/data/audio_chat_message/...` | `data/audio_chat_message/` |

---

## Ghi chú

- 🔒 = Endpoint yêu cầu JWT Bearer Token trong header `Authorization`
- Tất cả timestamp là UTC (ISO 8601)
- Xem Swagger UI đầy đủ tại `http://127.0.0.1:8000/docs`

---

*Tham khảo: [docs/02-system-architecture.md](02-system-architecture.md) | [docs/04-agent-design.md](04-agent-design.md)*

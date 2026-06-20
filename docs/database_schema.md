# Sơ đồ Cơ sở dữ liệu (Database Schema)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20  
> **Database**: MySQL – `ai_papers`  
> **Migration tool**: Alembic  
> **Tổng số bảng**: 10

---

## 1. ERD – Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o{ chat_sessions : "creates (CASCADE)"
    users ||--o{ notifications : "receives (CASCADE)"

    papers ||--o{ digest_papers : "listed in (CASCADE)"
    papers ||--o| audio_abstracts : "has 1-to-1 (CASCADE)"
    papers ||--o{ chat_sessions : "discussed in (CASCADE)"
    papers ||--o{ paper_topics : "associated with (CASCADE)"

    digests ||--o{ digest_papers : "contains (CASCADE)"
    digests ||--o{ notifications : "notified in (CASCADE)"

    chat_sessions ||--o{ chat_messages : "contains (CASCADE)"

    topics ||--o{ paper_topics : "categorizes (CASCADE)"

    users {
        bigint id PK
        varchar username UK
        varchar hashed_password
        varchar full_name
        varchar email UK
        boolean noti_daily
        datetime created_at
    }

    papers {
        bigint id PK
        varchar arxiv_id UK
        varchar title
        text abstract
        text summary
        json authors
        date published
        varchar pdf_path
        float score
        boolean has_audio
        datetime created_at
    }

    digests {
        bigint id PK
        date digest_date UK
        datetime created_at
    }

    digest_papers {
        bigint id PK
        bigint digest_id FK
        bigint paper_id FK
        int rank_position
        datetime created_at
    }

    audio_abstracts {
        bigint id PK
        bigint paper_id FK "UNIQUE"
        varchar file_path
        int duration_seconds
        json paper_timestamps
        datetime created_at
    }

    chat_sessions {
        bigint id PK
        bigint user_id FK
        bigint paper_id FK
        datetime created_at
    }

    chat_messages {
        bigint id PK
        bigint chat_session_id FK
        enum role
        text content
        varchar tts_path
        json tts_timestamps
        datetime created_at
    }

    topics {
        bigint id PK
        varchar name UK
        text description
        datetime created_at
    }

    paper_topics {
        bigint id PK
        bigint paper_id FK
        bigint topic_id FK
        float confidence_score
        datetime created_at
    }

    notifications {
        bigint id PK
        bigint user_id FK
        bigint digest_id FK
        enum channel
        enum status
        datetime sent_at
        text error_message
        datetime created_at
    }
```

---

## 2. Chi tiết từng bảng

### 2.1 Bảng `users`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | ID người dùng |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Tên đăng nhập |
| `hashed_password` | VARCHAR(255) | NOT NULL | Mật khẩu đã hash (bcrypt) |
| `full_name` | VARCHAR(100) | NULLABLE | Họ tên đầy đủ |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Email |
| `noti_daily` | BOOLEAN | DEFAULT TRUE | Nhận thông báo digest hàng ngày |
| `created_at` | DATETIME | DEFAULT NOW() | Thời điểm tạo |

### 2.2 Bảng `papers`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK, AUTO_INCREMENT | ID bài báo |
| `arxiv_id` | VARCHAR(50) | UNIQUE, NOT NULL | ID arXiv (e.g. `2312.01234`) |
| `title` | VARCHAR(500) | NOT NULL | Tiêu đề bài báo |
| `abstract` | TEXT | NULLABLE | Abstract gốc |
| `summary` | TEXT | NULLABLE | Tóm tắt học thuật (do Summarizer sinh) |
| `authors` | JSON | NULLABLE | Danh sách tác giả |
| `published` | DATE | INDEXED | Ngày xuất bản trên arXiv |
| `pdf_path` | VARCHAR(500) | NULLABLE | Đường dẫn tương đối file PDF |
| `score` | FLOAT | INDEXED | Điểm đánh giá nổi bật |
| `has_audio` | BOOLEAN | DEFAULT FALSE | Đã có audio abstract hay chưa |
| `created_at` | DATETIME | DEFAULT NOW(), INDEXED | Thời điểm import |

> **Lưu ý**: Không có cột `pdf_url` hay `updated_at`. `pdf_path` là đường dẫn tương đối (`data/paper_pdf/...`).

### 2.3 Bảng `digests`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | ID digest |
| `digest_date` | DATE | UNIQUE, NOT NULL | Ngày của digest (1 ngày = 1 digest) |
| `created_at` | DATETIME | DEFAULT NOW() | Thời điểm tạo |

### 2.4 Bảng `digest_papers` (Junction)

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `digest_id` | BIGINT | FK → digests(id) CASCADE | |
| `paper_id` | BIGINT | FK → papers(id) CASCADE | |
| `rank_position` | INT | CHECK 1–5 | Thứ hạng trong digest |
| `created_at` | DATETIME | DEFAULT NOW() | |

**Unique constraints:**
- `uq_digest_paper` → `(digest_id, paper_id)`
- `uq_digest_rank` → `(digest_id, rank_position)`

### 2.5 Bảng `audio_abstracts`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `paper_id` | BIGINT | FK → papers(id) CASCADE, **UNIQUE** | Quan hệ 1-1 với papers |
| `file_path` | VARCHAR(500) | NOT NULL | Đường dẫn file audio |
| `duration_seconds` | INT | NULLABLE | Thời lượng audio (giây) |
| `paper_timestamps` | JSON | NULLABLE | Timestamps của các chunk audio |
| `created_at` | DATETIME | DEFAULT NOW() | |

### 2.6 Bảng `chat_sessions`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | ID phiên chat |
| `user_id` | BIGINT | FK → users(id) CASCADE, INDEXED | |
| `paper_id` | BIGINT | FK → papers(id) CASCADE, INDEXED | |
| `created_at` | DATETIME | DEFAULT NOW() | |

### 2.7 Bảng `chat_messages`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `chat_session_id` | BIGINT | FK → chat_sessions(id) CASCADE, INDEXED | |
| `role` | ENUM('user','assistant','system') | NOT NULL | Vai trò người gửi |
| `content` | TEXT | NOT NULL | Nội dung tin nhắn |
| `tts_path` | VARCHAR(500) | NULLABLE | Đường dẫn audio cho message |
| `tts_timestamps` | JSON | NULLABLE | Timestamps TTS |
| `created_at` | DATETIME | DEFAULT NOW(), INDEXED | |

### 2.8 Bảng `topics`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `name` | VARCHAR(200) | UNIQUE, NOT NULL, INDEXED | Tên chủ đề AI |
| `description` | TEXT | NULLABLE | Mô tả chủ đề |
| `created_at` | DATETIME | DEFAULT NOW() | |

### 2.9 Bảng `paper_topics` (Junction)

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `paper_id` | BIGINT | FK → papers(id) CASCADE, INDEXED | |
| `topic_id` | BIGINT | FK → topics(id) CASCADE, INDEXED | |
| `confidence_score` | FLOAT | CHECK 0.0–1.0 | Độ tin cậy phân loại |
| `created_at` | DATETIME | DEFAULT NOW() | |

**Unique constraint:** `uq_paper_topic` → `(paper_id, topic_id)`

### 2.10 Bảng `notifications`

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | BIGINT | PK | |
| `user_id` | BIGINT | FK → users(id) CASCADE, INDEXED | |
| `digest_id` | BIGINT | FK → digests(id) CASCADE, NOT NULL, INDEXED | |
| `channel` | ENUM('email','web','system') | NOT NULL | Kênh gửi |
| `status` | ENUM('pending','sent','failed') | DEFAULT 'pending', INDEXED | Trạng thái |
| `sent_at` | DATETIME | NULLABLE, INDEXED | Thời điểm gửi |
| `error_message` | TEXT | NULLABLE | Thông báo lỗi nếu có |
| `created_at` | DATETIME | DEFAULT NOW() | |

**Unique constraint:** `uq_user_digest_channel` → `(user_id, digest_id, channel)`

---

## 3. Index tối ưu hóa

| # | Index Name | Bảng | Cột | Kiểu |
|---|---|---|---|---|
| 1 | auto | `papers` | `arxiv_id` | Unique |
| 2 | `idx_papers_published` | `papers` | `published` | Thường |
| 3 | `idx_papers_score` | `papers` | `score` | Thường |
| 4 | `idx_papers_created_at` | `papers` | `created_at` | Thường |
| 5 | `idx_digest_papers_digest_id` | `digest_papers` | `digest_id` | FK |
| 6 | `idx_digest_papers_paper_id` | `digest_papers` | `paper_id` | FK |
| 7 | `idx_digest_papers_rank_position` | `digest_papers` | `rank_position` | Thường |
| 8 | `idx_chat_sessions_user_id` | `chat_sessions` | `user_id` | FK |
| 9 | `idx_chat_sessions_paper_id` | `chat_sessions` | `paper_id` | FK |
| 10 | `idx_chat_messages_session_id` | `chat_messages` | `chat_session_id` | FK |
| 11 | `idx_chat_messages_created_at` | `chat_messages` | `created_at` | Thường |
| 12 | `idx_paper_topics_paper_id` | `paper_topics` | `paper_id` | FK |
| 13 | `idx_paper_topics_topic_id` | `paper_topics` | `topic_id` | FK |
| 14 | `idx_notifications_user_id` | `notifications` | `user_id` | FK |
| 15 | `idx_notifications_digest_id` | `notifications` | `digest_id` | FK |
| 16 | `idx_notifications_status` | `notifications` | `status` | Thường |
| 17 | `idx_notifications_sent_at` | `notifications` | `sent_at` | Thường |

---

## 4. Lệnh khởi tạo Database

```cmd
# 1. Tạo database rỗng
mysql -u root -p < scripts\init_db.sql

# 2. Cấu hình DATABASE_URL trong backend/.env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_papers

# 3. Chạy Alembic migrations
cd backend
.venv\Scripts\python.exe -m alembic upgrade head

# 4. Kiểm tra kết nối
curl http://127.0.0.1:8000/api/v1/system/db-health
```

---

*Tham khảo: [docs/system_architecture.md](system_architecture.md) | [scripts/reset_db.sql](../scripts/reset_db.sql)*

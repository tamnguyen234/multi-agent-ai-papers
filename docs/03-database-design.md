# 03. Thiết kế cơ sở dữ liệu (Database Design)

Tài liệu này mô tả chi tiết thiết kế cơ sở dữ liệu MySQL chuẩn hóa cho hệ thống **AI Paper Multi-Agent System** dựa trên mã script SQL thực tế đang chạy.

---

## 📊 Sơ đồ thực thể liên kết (Mermaid ERD)

Dưới đây là sơ đồ mối quan hệ giữa 11 bảng trong hệ thống:

```mermaid
erDiagram
    users ||--o{ chat_sessions : "creates (CASCADE)"
    users ||--o{ notifications : "receives (CASCADE)"
    
    papers ||--o{ digest_papers : "listed in (CASCADE)"
    papers ||--o| audio_abstracts : "has 1-to-1 (CASCADE)"
    papers ||--o{ chat_sessions : "discussed in (CASCADE)"
    papers ||--o{ paper_topics : "associated with (CASCADE)"
    
    digests ||--o{ digest_papers : "contains (CASCADE)"
    digests ||--o{ notifications : "notified in (SET NULL)"
    
    chat_sessions ||--o{ chat_messages : "contains (CASCADE)"
    
    topics ||--o{ paper_topics : "categorizes (CASCADE)"
    trend_runs ||--o{ paper_topics : "runs (SET NULL)"

    users {
        bigint id PK
        varchar username UK
        varchar hashed_password
        varchar full_name
        varchar email UK
        boolean noti_daily
        datetime created_at
        datetime updated_at
    }

    papers {
        bigint id PK
        varchar arxiv_id UK
        text title
        longtext abstract
        longtext summary
        json authors_json
        date published
        text arxiv_url
        text pdf_url
        varchar pdf_path
        varchar source
        varchar primary_category
        double trending_score
        json score_reason_json
        boolean has_audio
        datetime created_at
        datetime updated_at
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
        double score_at_digest
        datetime created_at
    }

    audio_abstracts {
        bigint id PK
        bigint paper_id FK "UNIQUE"
        varchar file_path
        double duration_seconds
        varchar voice
        varchar language
        varchar model_name
        json paper_timestamps_json
        datetime created_at
        datetime updated_at
    }

    chat_sessions {
        bigint id PK
        bigint user_id FK
        bigint paper_id FK
        datetime created_at
        datetime updated_at
    }

    chat_messages {
        bigint id PK
        bigint session_id FK
        enum role "user/assistant/system"
        longtext content
        json sources_json
        varchar tts_path
        json tts_timestamps_json
        double tts_duration_seconds
        datetime created_at
    }

    topics {
        bigint id PK
        varchar name UK
        text description
        json keywords_json
        datetime created_at
        datetime updated_at
    }

    trend_runs {
        bigint id PK
        int window_days
        date date_from
        date date_to
        int paper_count
        varchar mode
        enum status "running/success/failed"
        text error_message
        datetime started_at
        datetime finished_at
    }

    paper_topics {
        bigint id PK
        bigint paper_id FK
        bigint topic_id FK
        bigint trend_run_id FK
        double confidence_score
        datetime created_at
    }

    notifications {
        bigint id PK
        bigint user_id FK
        bigint digest_id FK
        enum channel "email/in_app"
        enum status "pending/sent/failed"
        varchar recipient
        varchar title
        longtext message
        datetime sent_at
        text error_message
        datetime created_at
    }
```

---

## 📋 Chi tiết các bảng (Tables Metadata)

### 1. Bảng `users`
- **Mục đích**: Quản lý tài khoản người dùng và nhận thông báo hàng ngày.
- **Khóa chính**: `id` kiểu `BIGINT`.
- **Cột `noti_daily`**: Kiểu `BOOLEAN`, mặc định `TRUE` (server_default `'true'`).

### 2. Bảng `papers`
- **Mục đích**: Lưu trữ thông tin bài báo khoa học cào từ arXiv.
- **Cột `published`**: Kiểu `DATE`, lưu ngày phát hành bài viết trên arXiv (index).
- **Lưu ý**: Đường dẫn tài liệu PDF được lưu trong `pdf_path` là đường dẫn tương đối (relative path). Chứa `pdf_url` (đường dẫn PDF gốc trên arXiv) và `updated_at` (thời điểm cập nhật cuối).

### 3. Bảng `digests`
- **Mục đích**: Bản tin tổng hợp top 5 bài viết nổi bật hàng ngày.
- **Cột `digest_date`**: Kiểu `DATE` độc nhất (`UNIQUE`), làm index tìm kiếm.

### 4. Bảng `digest_papers` (Bảng trung gian)
- **Mục đích**: Ánh xạ nhiều-nhiều giữa Digests và Papers.
- **Cột `rank_position`**: Thứ hạng trending trong ngày của bài báo (giá trị từ 1 đến 5).
- **Ràng buộc**:
  - `uq_digest_paper`: Unique kép `(digest_id, paper_id)`.
  - `uq_digest_rank`: Unique kép `(digest_id, rank_position)`.
  - `chk_digest_rank_position`: CheckConstraint `rank_position BETWEEN 1 AND 5`.
- **Khóa ngoại**: Cascade delete trỏ đến `digests(id)` và `papers(id)`.

### 5. Bảng `audio_abstracts`
- **Mục đích**: Lưu trữ file âm thanh tóm tắt học thuật của một bài viết.
- **Thiết kế quan hệ 1-1**:
  - Cột `paper_id` được đặt là **`UNIQUE`** và NOT NULL.
  - Thông tin mốc thời gian (timestamps) của các chunk được lưu tập trung trong cột `paper_timestamps_json` (JSON format).
- **Khóa ngoại**: Cascade delete trỏ đến `papers(id)`.

### 6. Bảng `chat_sessions`
- **Mục đích**: Phiên hội thoại hỏi đáp Q&A giữa người dùng và bài báo.
- **Khóa ngoại**: `user_id` và `paper_id` (đều được đánh index phục vụ truy vấn lịch sử chat nhanh).
- **Ràng buộc**: `uq_chat_session_user_paper`: Unique kép `(user_id, paper_id)`.

### 7. Bảng `chat_messages`
- **Mục đích**: Chi tiết các câu hỏi và câu trả lời trong phiên chat.
- **Cột `session_id`**: Khóa ngoại liên kết với `chat_sessions(id)`.
- **Cột `role`**: Kiểu dữ liệu `sa.Enum` (`user`, `assistant`, `system`).
- **Cột `sources_json`**: Chứa thông tin tài liệu tham khảo/trích dẫn PDF dưới dạng JSON.
- **Cột `tts_path`**: Đường dẫn tương đối file audio phát âm của tin nhắn (nếu có).

### 8. Bảng `topics`
- **Mục đích**: Phân loại các chủ đề công nghệ AI đang nổi bật.
- **Cột `keywords_json`**: Chứa danh sách các từ khóa đại diện của chủ đề.

### 9. Bảng `trend_runs`
- **Mục đích**: Quản lý lịch sử chạy của Agent phân tích xu hướng chủ đề.
- **Trạng thái**: Chứa cột `status` kiểu Enum (`running`, `success`, `failed`).

### 10. Bảng `paper_topics` (Bảng trung gian)
- **Mục đích**: Ánh xạ bài báo vào chủ đề công nghệ và lượt chạy xu hướng.
- **Ràng buộc**:
  - `uq_paper_topic`: Unique kép `(paper_id, topic_id)`.
  - `chk_confidence_score` (gián tiếp thông qua float type): Thể hiện độ tin cậy từ 0.0 đến 1.0.

### 11. Bảng `notifications`
- **Mục đích**: Nhật ký gửi thông báo hằng ngày.
- **Ràng buộc**:
  - `uq_notification_user_digest_channel`: Unique trên 3 cột `(user_id, digest_id, channel)`.
  - `channel` dùng Enum: `email`, `in_app`.
  - `status` dùng Enum: `pending`, `sent`, `failed`.

---

## ⚡ Danh sách các Index được tối ưu hóa

Hệ thống tự động thiết lập các chỉ mục sau để tăng tốc độ truy vấn:
1. `idx_papers_arxiv_id` (Unique index trên `papers.arxiv_id`)
2. `idx_papers_published` (Index trên `papers.published`)
3. `idx_papers_trending_score` (Index trên `papers.trending_score`)
4. `idx_papers_created_at` (Index trên `papers.created_at`)
5. `idx_digests_digest_date` (Index trên `digests.digest_date`)
6. `idx_digest_papers_digest_id` (Index trên khóa ngoại `digest_papers.digest_id`)
7. `idx_digest_papers_paper_id` (Index trên khóa ngoại `digest_papers.paper_id`)
8. `idx_audio_abstracts_paper_id` (Index trên khóa ngoại `audio_abstracts.paper_id`)
9. `idx_chat_sessions_user_id` (Index trên khóa ngoại `chat_sessions.user_id`)
10. `idx_chat_sessions_paper_id` (Index trên khóa ngoại `chat_sessions.paper_id`)
11. `idx_chat_messages_session_id` (Index trên khóa ngoại `chat_messages.session_id`)
12. `idx_chat_messages_role` (Index trên `chat_messages.role`)
13. `idx_chat_messages_created_at` (Index trên `chat_messages.created_at`)
14. `idx_topics_name` (Index trên `topics.name`)
15. `idx_trend_runs_status` (Index trên `trend_runs.status`)
16. `idx_trend_runs_started_at` (Index trên `trend_runs.started_at`)
17. `idx_paper_topics_paper_id` (Index trên khóa ngoại `paper_topics.paper_id`)
18. `idx_paper_topics_topic_id` (Index trên khóa ngoại `paper_topics.topic_id`)
19. `idx_paper_topics_trend_run_id` (Index trên khóa ngoại `paper_topics.trend_run_id`)
20. `idx_notifications_user_id` (Index trên khóa ngoại `notifications.user_id`)
21. `idx_notifications_digest_id` (Index trên khóa ngoại `notifications.digest_id`)
22. `idx_notifications_status` (Index trên `notifications.status`)
23. `idx_notifications_created_at` (Index trên `notifications.created_at`)

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
```

---

*Tham khảo: [docs/02-system-architecture.md](02-system-architecture.md)*

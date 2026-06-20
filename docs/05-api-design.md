# 05. Thiết kế giao diện API (API Design)

Tài liệu này định nghĩa thiết kế API cho giao tiếp giữa Frontend và Backend Gateway.

---

## 🔐 1. Nhóm API Xác thực (Authentication)

### `POST /api/v1/auth/register`
- **Mô tả**: Đăng ký tài khoản người dùng mới.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "strongpassword123",
    "name": "Nguyen Van A"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "message": "User registered successfully",
    "user_id": 1
  }
  ```

### `POST /api/v1/auth/login`
- **Mô tả**: Đăng nhập hệ thống và lấy JWT token.
- **Request Body**: Form-data (`username`, `password`).
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

---

## 📄 2. Nhóm API Quản lý Bài Báo (AI Papers)

### `GET /api/v1/papers`
- **Mô tả**: Lấy danh sách các bài báo AI đã tải.
- **Query Parameters**: `skip` (mặc định 0), `limit` (mặc định 20).
- **Response (200 OK)**:
  ```json
  {
    "papers": [
      {
        "id": 1,
        "arxiv_id": "2403.0001",
        "title": "Attention Is All You Need",
        "authors": "Ashish Vaswani, et al.",
        "publish_date": "2017-06-12",
        "status": "summarized",
        "audio_path": "/data/audio_abstract/2403.0001.mp3"
      }
    ]
  }
  ```

### `GET /api/v1/papers/{paper_id}`
- **Mô tả**: Xem chi tiết bài báo kèm bản tóm tắt học thuật.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models...",
    "summary": "### Key Findings\n- Introduced Transformer model...\n- Replaced recurrent layers with self-attention...",
    "pdf_path": "/data/paper_pdf/2403.0001.pdf",
    "audio_path": "/data/audio_abstract/2403.0001.mp3"
  }
  ```

---

## 💬 3. Nhóm API Hỏi Đáp (RAG Chat)

### `POST /api/v1/chat/{paper_id}`
- **Mô tả**: Gửi câu hỏi tương tác với bài báo PDF.
- **Request Body**:
  ```json
  {
    "message": "Cơ chế Self-Attention hoạt động như thế nào?"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "reply": "Self-attention cho phép mô hình liên kết mỗi từ trong chuỗi với các từ khác để hiểu ngữ cảnh...",
    "audio_url": "/data/audio_chat_message/chat_1_reply.mp3"
  }
  ```

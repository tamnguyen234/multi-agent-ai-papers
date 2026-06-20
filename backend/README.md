# AI Paper Multi-Agent Backend

Đây là module Backend chính của hệ thống **AI Paper Multi-Agent System**. Nó hoạt động như một **API Gateway** cung cấp endpoints cho Frontend, đồng thời tích hợp **Scheduler** (chạy ngầm) để tự động hóa quy trình hàng ngày và gọi đến các Agent AI độc lập.

---

## 🛠️ Vai trò của Backend
1. **API Gateway**: Định tuyến yêu cầu từ Frontend đến các Agent thích hợp (Summarizer, Trend, Q&A, TTS).
2. **Authentication**: Quản lý đăng ký, đăng nhập người dùng bằng JWT (JSON Web Tokens).
3. **Database Management**: Kết nối cơ sở dữ liệu MySQL, định nghĩa ORM models bằng SQLAlchemy.
4. **Data Management Service**: Quản lý metadata và đường dẫn lưu trữ tương đối của các file PDF & Audio.
5. **Daily Scheduler**: Sử dụng `APScheduler` để định kỳ 2h sáng gọi Summarizer Agent, tải bài báo, tạo audio và gửi thông báo qua Email.

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định: `8000` (URL: `http://localhost:8000`)

---

## 🚀 Hướng dẫn khởi chạy

### 1. Chuẩn bị môi trường Python
Khuyên dùng môi trường ảo `venv` để tránh xung đột thư viện:
```bash
# Di chuyển vào thư mục backend
cd backend

# Khởi tạo môi trường ảo
python -m venv .venv

# Kích hoạt môi trường ảo (Windows)
.venv\Scripts\activate

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

### 2. Thiết lập cấu hình `.env`
Sao chép `.env.example` và sửa đổi thông số kết nối Database, SMTP Gmail và URLs của các Agent:
```bash
cp .env.example .env
```

### 3. Chạy Database Migrations (Alembic)
Trước khi khởi động server, đảm bảo bạn đã tạo cơ sở dữ liệu `ai_papers` rỗng (ví dụ: `mysql -u root -p < scripts\init_db.sql`). Sau đó thực thi Alembic migration để tự động tạo lập 10 bảng dữ liệu:
```bash
alembic upgrade head
```

### 4. Chạy Server ở chế độ Development
Chạy backend với Uvicorn tự động reload khi mã nguồn thay đổi:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Sau đó truy cập tài liệu API tự động tại:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Bạn có thể kiểm tra trạng thái kết nối Database tại endpoint chẩn đoán:
- DB Diagnostics: `http://127.0.0.1:8000/api/v1/system/db-health`

---

## 📁 Cấu trúc thư mục của Backend
- `/app/main.py`: Khởi chạy FastAPI application.
- `/app/core/`: Lưu trữ cấu hình hệ thống (`config.py`), cài đặt bảo mật JWT (`security.py`).
- `/app/db/`: Cài đặt DB engine (`database.py`) và định nghĩa các Models (`models/`).
- `/app/api/`: Các router REST API phân theo phiên bản (v1).
- `/app/services/`: Logic nghiệp vụ (Auth, Paper management, Notification, Storage).
- `/app/agents/`: Client kết nối HTTP đến các Agents độc lập.
- `/app/jobs/`: Định nghĩa các Cron Jobs chạy ngầm định kỳ.

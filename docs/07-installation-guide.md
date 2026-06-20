# 07. Hướng dẫn cài đặt và thiết lập môi trường (Installation Guide)

Tài liệu này hướng dẫn chi tiết quy trình thiết lập môi trường và khởi chạy hệ thống **AI Paper Multi-Agent System** trên hệ điều hành Windows ở chế độ **Skeleton Service (Health Check Mode)**.

---

## 💻 Yêu cầu hệ thống tối thiểu
- **Hệ điều hành**: Windows 10 / 11.
- **Python**: Phiên bản `>= 3.10` (Hệ thống hiện tại đã xác minh chạy **Python 3.10.9**).
- **Git**: Phục vụ việc clone mã nguồn.
- **Database**: MySQL Server cục bộ hoặc chạy qua Docker Desktop.
- **Node.js**: Phiên bản `>= 18.x` (Dành cho việc cài đặt Frontend ở các task sau).

---

## ⚙️ Cài đặt môi trường tự động (Quick Start)

Chúng tôi cung cấp script thiết lập tự động giúp sao chép file cấu hình, tạo môi trường ảo Python và cài đặt các dependencies tối thiểu cho cả 5 service (Backend + 4 Agent).

### 🚀 Cách chạy script setup:
1. Mở Command Prompt hoặc PowerShell tại thư mục gốc của dự án:
   ```cmd
   cd /d d:\TTCS-multiagent\ai-paper-multi-agent-system
   ```
2. Thực thi một trong các script thiết lập sau:
   - **Bằng Windows Batch Script**:
     ```cmd
     scripts\setup_env.bat
     ```
   - **Bằng PowerShell Script**:
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts\setup_env.ps1
     ```

---

## 🗄️ Quy trình thiết lập Cơ sở dữ liệu (Database Workflow)

Để khởi tạo cấu trúc cơ sở dữ liệu MySQL, vui lòng thực hiện tuần tự theo quy trình sau:

### Bước 1: Khởi tạo Database rỗng
Mở Command Prompt và chạy lệnh dưới đây để tạo cơ sở dữ liệu `ai_papers` trống:
```cmd
mysql -u root -p < scripts\init_db.sql
```
*(Nếu database `ai_papers` đã tồn tại bảng cũ và bạn muốn xóa sạch làm lại từ đầu ở môi trường development, bạn có thể thay thế lệnh trên bằng file reset: `mysql -u root -p < scripts\reset_db.sql`)*.

### Bước 2: Cấu hình biến môi trường
Mở file `backend/.env` trên máy cục bộ của bạn và cấu hình thông số kết nối cơ sở dữ liệu (bao gồm cả mật khẩu thực):
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_papers
DB_USER=root
DB_PASSWORD=your_actual_db_password
```
> [!IMPORTANT]
> **Quy tắc bảo mật**:
> - Chỉ được ghi mật khẩu thật của bạn vào file `backend/.env` cục bộ.
> - Tuyệt đối không đưa mật khẩu thật vào bất kỳ file SQL, file code Python, README, hay file `.env.example`.
> - Các file `.env` đã được ignore tự động, tuyệt đối không commit lên Git.

### Bước 3: Chạy Alembic Database Migrations
Alembic là công cụ chính chịu trách nhiệm tạo lập cấu trúc các bảng. Sau khi database rỗng đã có, thực thi lệnh sau:
```cmd
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
```
Sau khi hoàn tất, database của bạn sẽ tự động được tạo đầy đủ 10 bảng quan hệ (`users`, `papers`, `digests`...).

### Bước 4: Kiểm tra trạng thái kết nối Database (DB Health)
Khởi chạy Backend Gateway:
```cmd
cd ..
scripts\run_backend.bat
```
Kiểm tra kết nối bằng cách nhấp đúp chuột vào file script [scripts/check_db_connection.bat](file:///d:/TTCS-multiagent/ai-paper-multi-agent-system/scripts/check_db_connection.bat) hoặc chạy lệnh:
```cmd
curl http://127.0.0.1:8000/api/v1/system/db-health
```
Kết quả phản hồi thành công mong muốn:
```json
{"status": "ok", "database": "connected"}
```

---

## 🚀 Khởi chạy hệ thống toàn cục

Hệ thống hỗ trợ chạy đồng thời cả API Gateway và 4 Agent chuyên biệt trong các cửa sổ terminal riêng biệt để bạn dễ dàng theo dõi log:

1. Chạy file script từ thư mục gốc của dự án:
   ```cmd
   scripts\run_all.bat
   ```
2. Lệnh này sẽ mở song song 5 cửa sổ Command Prompt cho:
   - **Backend Gateway** (Port `8000`)
   - **Summarizer Agent** (Port `8101`)
   - **Trend Agent** (Port `8102`)
   - **Q&A Agent** (Port `8103`)
   - **TTS Agent** (Port `8104`)

---

## 🩺 Kiểm tra sức khỏe dịch vụ (Health Check)

Để kiểm tra xem toàn bộ các thành phần trong hệ thống đã khởi động và hoạt động bình thường hay chưa:

1. Chạy script kiểm tra:
   ```cmd
   scripts\check_health.bat
   ```
2. Kết quả phản hồi hợp lệ cho tất cả các service là:
   ```json
   {"status":"ok"}
   ```
   
### 🔌 Danh sách Endpoint kiểm tra sức khỏe:
- **Backend Gateway**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Summarizer Agent**: [http://127.0.0.1:8101/health](http://127.0.0.1:8101/health)
- **Trend Agent**: [http://127.0.0.1:8102/health](http://127.0.0.1:8102/health)
- **Q&A Agent**: [http://127.0.0.1:8103/health](http://127.0.0.1:8103/health)
- **TTS Agent**: [http://127.0.0.1:8104/health](http://127.0.0.1:8104/health)

# 07. Hướng dẫn cài đặt và thiết lập môi trường (Installation Guide)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20  
> **Môi trường mục tiêu**: Local Development / Demo (Windows)

---

## 1. Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu | Ghi chú |
|---|---|---|
| OS | Windows 10 / 11 | Scripts `.bat` tối ưu cho Windows |
| Python | 3.10+ | Đã xác minh với 3.10.9 |
| Node.js | 18.x+ | Cho Frontend React/Vite |
| MySQL | 8.0+ | Hoặc chạy qua Docker |
| Git | Bất kỳ | Clone mã nguồn |
| RAM | 8 GB tối thiểu | 16 GB nếu dùng real AI mode |
| Disk | 10 GB+ | Cho venv + model weights |

---

## 2. Cài đặt lần đầu (First-time Setup)

### Bước 1 – Clone mã nguồn và di chuyển vào thư mục dự án

```cmd
git clone <repo-url>
cd d:\multi-agent-ai
```

### Bước 2 – Cấu hình biến môi trường

Sao chép file mẫu và chỉnh sửa:

```cmd
# Root level (dùng cho tham khảo)
copy .env.example .env

# Backend
copy backend\.env.example backend\.env

# Frontend
copy frontend\.env.example frontend\.env
```

Chỉnh sửa `backend/.env`:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/ai_papers
JWT_SECRET_KEY=your-secret-key-at-least-32-chars
```

Chỉnh sửa `frontend/.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> [!CAUTION]
> Tuyệt đối không commit file `.env` lên Git.  
> Các file `.env` đã được liệt kê trong `.gitignore`.

### Bước 3 – Setup tự động

```cmd
scripts\setup_env.bat
```

Script này sẽ:
1. Tạo Python venv cho Backend + 4 Agents
2. Cài đặt `requirements.txt` cho từng thành phần
3. Cài đặt `node_modules` cho Frontend

### Bước 4 – Khởi tạo Database

```cmd
# Tạo database rỗng
mysql -u root -p < scripts\init_db.sql

# Chạy Alembic migrations
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

Kiểm tra:
```cmd
curl http://127.0.0.1:8000/api/v1/system/db-health
```

---

## 3. Khởi chạy hệ thống

### Cách 1 – Script tự động (Khuyến nghị)

Khởi chạy toàn bộ hệ thống (bao gồm cả Ollama, Backend, các Agents và Frontend) bằng một lệnh duy nhất:
```cmd
scripts\run_all.bat
```
*Lưu ý: Bạn có thể chọn khởi chạy riêng lẻ từng thành phần bằng cách truyền tham số:*
- Chỉ chạy Ollama: `scripts\run_all.bat --ollama`
- Chỉ chạy Backend: `scripts\run_all.bat --backend`
- Chỉ chạy các Agents: `scripts\run_all.bat --agents`
- Chỉ chạy Frontend: `scripts\run_all.bat --frontend`

### Cách 2 – Thủ công (để debug)

```cmd
# Terminal 1 – Backend (Port 8000)
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 – Summarizer Agent (Port 8101)
cd agents\summarizer_agent
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8101

# Terminal 3 – Trend Agent (Port 8102)
cd agents\trend_agent
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8102

# Terminal 4 – Q&A Agent (Port 8103)
cd agents\qa_agent
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8103

# Terminal 5 – TTS Agent (Port 8104)
cd agents\tts_agent
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8104

# Terminal 6 – Frontend
cd frontend
npm run dev
```

### URL truy cập

| Thành phần | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| Summarizer Agent | http://127.0.0.1:8101 |
| Trend Agent | http://127.0.0.1:8102 |
| QA Agent | http://127.0.0.1:8103 |
| TTS Agent | http://127.0.0.1:8104 |

---

## 4. Kiểm tra sức khỏe hệ thống

Kiểm tra thủ công qua các endpoint health check của hệ thống:
```cmd
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/system/db-health
curl http://127.0.0.1:8101/health
curl http://127.0.0.1:8102/health
curl http://127.0.0.1:8103/health
curl http://127.0.0.1:8104/health
```

---

## 5. Chế độ vận hành (Execution Modes)

### Mock Fallback Mode (Mặc định – Khuyến nghị cho demo)

Trong `backend/.env`:
```env
SUMMARIZER_MODE=mock_fallback
TREND_MODE=rule_based_fallback
QA_MODE=mock_fallback
TTS_MODE=mock_fallback
```

**Ưu điểm**: Không cần GPU, không cần download AI model, khởi động nhanh.

### Real Mode (Cần phần cứng mạnh)

```env
SUMMARIZER_MODE=real       # Cần: transformers, torch, ~4GB model
TREND_MODE=bertopic        # Cần: bertopic, umap-learn, hdbscan
QA_MODE=real               # Cần: Ollama server + qwen3.5:4b + nomic-embed-text
TTS_MODE=real              # Cần: torch, transformers TTS model
```

**Yêu cầu thêm cho real mode:**
- Ollama server chạy tại `http://localhost:11434`
  ```cmd
  ollama serve
  ollama pull qwen3.5:4b
  ollama pull nomic-embed-text
  ```
- GPU CUDA (tùy chọn nhưng giúp tăng tốc đáng kể)

---

## 6. Database Operations

### Seed dữ liệu mẫu
```cmd
# Qua API
curl -X POST http://127.0.0.1:8000/api/v1/dev/seed-papers

# Qua SQL
mysql -u root -p ai_papers < scripts\seed_data.sql
```

### Reset database
```cmd
mysql -u root -p < scripts\reset_db.sql
```

> [!WARNING]
> `reset_db.sql` xóa toàn bộ dữ liệu và tạo lại schema. Chỉ dùng trong môi trường development.

### Backup database (trước khi demo)
```cmd
mysqldump -u root -p ai_papers > backup_ai_papers.sql
```

---

## 7. Frontend Build (Production Check)

```cmd
cd frontend
npm run build
```

Kết quả build nằm tại `frontend/dist/` – **không commit** lên Git.

---

## 8. Cấu trúc file tĩnh

Backend serve static files:
```python
app.mount("/static/data", StaticFiles(directory=str(DATA_DIR)), name="static_data")
```

Đường dẫn file trong DB là **relative path** (ví dụ: `data/paper_pdf/2312.01234.pdf`).  
URL truy cập frontend: `http://127.0.0.1:8000/static/data/paper_pdf/2312.01234.pdf`

---

## 9. Lưu ý bảo mật

> [!CAUTION]
> **Không bao giờ commit:**
> - `.env` files (bất kỳ cấp nào)
> - File PDF trong `data/paper_pdf/`
> - File audio trong `data/audio_*/`
> - FAISS indexes trong `data/indices_v2/`
> - `node_modules/`, `.venv/`, `dist/`, `build/`

Kiểm tra trước khi commit:
```cmd
git status
git diff --staged
```

Kiểm tra không có file nhạy cảm bị track:
```cmd
git ls-files | findstr ".env"
git ls-files | findstr "data\"
```

---

## 10. Khắc phục sự cố thường gặp

### Backend không kết nối được Database
```
sqlalchemy.exc.OperationalError: Can't connect to MySQL
```
**Giải pháp**: Kiểm tra MySQL đang chạy, DATABASE_URL đúng trong `backend/.env`.

### CORS Error trên Frontend
```
Access-Control-Allow-Origin error
```
**Giải pháp**: Đảm bảo Frontend chạy ở `http://localhost:5173` (không phải `127.0.0.1:5173`).

### Agent không phản hồi (timeout)
```
httpx.TimeoutException
```
**Giải pháp**: Agent chưa khởi động, hoặc đang load model. Chờ 30-60 giây.

### Summarizer timeout (120s)
**Giải pháp**: Lần đầu download BART/T5 model (~1.6GB). Chờ download xong, lần sau nhanh hơn.

### Lỗi: Port bị chiếm (WinError 10013 / Address already in use)

```
ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
ERROR: [Errno 10048] error while attempting to bind on address
```

**Nguyên nhân**: Service cũ chưa tắt hẳn, hoặc một ứng dụng khác đang dùng cổng đó.

**Cách xử lý theo thứ tự:**
```cmd
# Bước 1: Kill toàn bộ process trên project ports
scripts\kill_project_ports.bat

# Bước 2: Khởi chạy lại hệ thống
scripts\run_all.bat
```

Hoặc kill thủ công một port cụ thể:
```cmd
netstat -ano | findstr ":8000 " | findstr "LISTENING"
taskkill /PID <PID> /F
```

### Lỗi: Port 5173 bị chiếm, Vite chạy sang 5174

```
Port 5173 is in use, trying another one...
Local: http://localhost:5174/
```

**Nguyên nhân**: Vite trước đó chưa tắt sạch, hoặc một ứng dụng khác đang bind port 5173.

**Cách xử lý:**
```cmd
scripts\kill_project_ports.bat
scripts\run_all.bat --frontend
```

`run_all.bat --frontend` hiện dùng `--strictPort` nên sẽ báo lỗi rõ thay vì nhảy sang 5174.

---

### Lỗi: `'A' is not recognized as an internal or external command`

```
'A' is not recognized as an internal or external command, operable program or batch file.
```

**Nguyên nhân**: File `.bat` chứa ký tự `&` không escape trong chuỗi như `Q&A`. Trong Windows CMD, `&` là ký tự nối lệnh, nên `echo Q&A` bị tách thành lệnh `echo Q` và lệnh `A`.

**Cách xử lý**: Tất cả scripts trong `scripts/` đã được sửa để thay `Q&A` → `QA`. Nếu gặp lỗi này ở script tùy chỉnh khác, thay `Q&A` → `QA` hoặc escape thành `Q^&A` trong CMD echo.

---

## 11. Scripts quản lý port

| Script | Chức năng |
|---|---|
| `scripts\kill_project_ports.bat` | Kill process LISTENING trên các port của project. In kết quả kill từng port. |

---

*Tham khảo: [docs/08-demo-scenarios.md](08-demo-scenarios.md) | [docs/02-system-architecture.md](02-system-architecture.md)*

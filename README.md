# AI Paper Multi-Agent System

Hệ thống **Quản lý Multi-Agent tương tác Bài báo AI** là một giải pháp tự động hóa quy trình: thu thập bài báo AI thật từ arXiv → sinh tóm tắt → phân tích xu hướng chủ đề → hỗ trợ hỏi đáp RAG trên nội dung bài báo → chuyển đổi văn bản sang giọng nói (TTS) tiếng Việt chất lượng cao.

Dự án hoạt động hoàn toàn bằng **dữ liệu thật** từ arXiv, hỗ trợ sinh audio tóm tắt theo cơ chế lazy-generation trên giao diện web.

---

## 🗺️ Kiến trúc hệ thống

Dự án bao gồm các thành phần microservices chạy song song và giao tiếp qua REST API:

1. **Frontend (React + Vite + TypeScript)** (Cổng `5173`): Giao diện người dùng hiện đại, cung cấp trang Dashboard hiển thị Digest hàng ngày, danh sách bài báo, giao diện chat hỏi đáp PDF với audio player và phân tích biểu đồ xu hướng (Trends).
2. **Backend Gateway (FastAPI + APScheduler)** (Cổng `8000`): Cổng điều phối trung tâm, quản lý định tuyến, xác thực JWT, lập lịch công việc (APScheduler) chạy lúc 2:00 AM hàng ngày và lưu trữ cơ sở dữ liệu.
3. **Summarizer Agent** (Cổng `8101`): Thu thập tin tức từ arXiv RSS feed, tải PDF và sử dụng model BART/T5 để sinh tóm tắt chất lượng cao.
4. **Trend Agent** (Cổng `8102`): Phân tích phân cụm chủ đề bài báo bằng thuật toán BERTopic, UMAP, HDBSCAN kết hợp sentence-transformers.
5. **Q&A Agent (LangChain + FAISS + Ollama)** (Cổng `8103`): Xây dựng cơ sở tri thức vector RAG từ file PDF của bài báo. Tích hợp với **Ollama portable** chạy model `qwen2.5:3b` offline để trả lời câu hỏi của người dùng.
6. **TTS Agent (VieNeu)** (Cổng `8104`): Chuyển đổi văn bản tóm tắt/chat sang audio tiếng Việt sử dụng voice Ngọc Linh (nữ) hoặc Gia Bảo (nam).
7. **Database & Storage (MySQL + Local File Storage)**: Lưu trữ 10 bảng dữ liệu MySQL đồng bộ qua **Alembic migrations** và lưu trữ file tĩnh (PDFs, audio, indexes) trong thư mục `data/`.

---

## ⚡ Quick Start

### 1. Cấu hình môi trường
Sao chép tệp cấu hình mẫu và điền các tham số kết nối MySQL cục bộ của bạn:
```cmd
copy .env.example .env
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```
*Chỉnh sửa `backend/.env` để cập nhật mật khẩu cơ sở dữ liệu:*
```env
DATABASE_URL=mysql+pymysql://root:MAT_KHAU_CUA_BAN@localhost:3306/ai_papers
```

### 2. Setup tự động (venv & dependencies)
Khởi tạo các môi trường ảo Python cho backend và các agents, đồng thời cài đặt các thư viện cần thiết:
*   Cài đặt chế độ **Health-check** (mặc định):
    ```cmd
    scripts\setup_env.bat
    ```
*   Cài đặt chế độ **Full** (đầy đủ cho Real Mode):
    ```cmd
    scripts\setup_env.bat --full
    ```

### 3. Khởi tạo Database
Tạo cơ sở dữ liệu MySQL và áp dụng migrations:
```cmd
mysql -u root -p < scripts\init_db.sql
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

### 4. Khởi chạy toàn bộ hệ thống
Khởi chạy toàn bộ các thành phần hệ thống chỉ bằng một lệnh duy nhất:
```cmd
scripts\run_all.bat
```
*Lưu ý: Bạn có thể chọn khởi chạy riêng lẻ từng dịch vụ bằng cách truyền tham số:*
- Chỉ chạy Ollama: `scripts\run_all.bat --ollama`
- Chỉ chạy Backend Gateway: `scripts\run_all.bat --backend`
- Chỉ chạy 4 AI Agents: `scripts\run_all.bat --agents`
- Chỉ chạy Frontend: `scripts\run_all.bat --frontend`

---

## 📊 Chế độ Dữ liệu thật (Real-Data Mode)

Hệ thống được cấu hình chạy hoàn toàn bằng **dữ liệu bài báo thật** (103 bài báo arXiv thật, 20 Daily Digests liên tiếp, 0 bài báo mock/demo).

> [!NOTE]
> Theo cấu hình `.gitignore`, toàn bộ thư mục chứa tệp dữ liệu thật phát sinh (`data/paper_pdf/**`, `data/audio_abstract/**`, `data/audio_chat_message/**`, `data/faiss_indexes/**`) được loại trừ khỏi Git để tránh commit tệp nhị phân nặng lên kho chứa. Dữ liệu này được tạo và lưu trữ cục bộ trên máy chạy.

### Lệnh khởi tạo/tái tạo bộ dữ liệu 100 bài báo thật
Nếu bạn muốn tải lại hoặc tạo mới bộ dữ liệu mô phỏng 20 ngày chạy liên tục (mỗi ngày 5 bài báo thật):
```cmd
backend\.venv\Scripts\python.exe backend/scripts/backfill_arxiv_daily_digests.py --days 20 --per-day 5 --force
```

### Lazy Audio Abstract Generation
Để tối ưu hóa thời gian chạy và băng thông, audio abstract được sinh theo cơ chế **lazy-generation (on-demand)**. 
- Khi người dùng truy cập trang chi tiết bài báo chưa có audio, nút **"Tạo audio abstract"** sẽ hiển thị.
- Khi nhấn nút, frontend gọi API `POST /api/v1/papers/{paper_id}/audio-abstract` để yêu cầu TTS Agent tổng hợp âm thanh thực tế, lưu DB và trả về player nghe trực tiếp.
- Các lần gọi tiếp theo sẽ trả về file cache tĩnh (chế độ `existing`) giúp tối ưu hiệu năng.

---

## 🛠️ Công cụ bảo trì & quản trị (Maintenance Commands)

Hệ thống cung cấp sẵn các CLI quản trị chạy bằng python ảo của backend:

* **Kiểm tra tính nhất quán dữ liệu thật**:
  ```cmd
  backend\.venv\Scripts\python.exe backend/scripts/verify_real_data_mode.py
  ```
* **Dọn dẹp mock/demo database**:
  Loại bỏ các dữ liệu kiểm thử cũ, reassign digest sang bài báo thật và di chuyển tệp mock vào thư mục rác an toàn:
  ```cmd
  backend\.venv\Scripts\python.exe backend/scripts/clean_mock_demo_data.py --apply --yes-i-understand --clean-orphans --clean-chat-demo --backup-report
  ```
* **Dọn dẹp tệp tin rác project**:
  Tự động quét, phân tích tham chiếu trong codebase và di chuyển các thư mục trùng lặp (`multi_agent/`), pycache, log rác vào `_cleanup_trash/` mà không ảnh hưởng tới code runtime và real data:
  ```cmd
  backend\.venv\Scripts\python.exe scripts/clean_project_files.py --apply --yes-i-understand --include-cache --include-demo --include-old-logs --include-old-screenshots
  ```
* **Chạy kiểm thử toàn bộ hệ thống (Full Pipeline Test)**:
  Tự động hóa 28 bước kiểm tra sức khỏe của Gateway, Agents, tạo digest, phân tích xu hướng, QA chat RAG và sinh audio:
  ```cmd
  backend\.venv\Scripts\python.exe scripts/test_full_pipeline.py
  ```

---

## 🔍 Hướng dẫn sửa lỗi nhanh (Troubleshooting)

1. **Ollama không kết nối được (Cổng 11434)**:
   - Hãy chạy `scripts\check_ollama.bat` để chẩn đoán. Đảm bảo Ollama đã tải và chạy được model `qwen2.5:3b` cục bộ.
2. **Lỗi Timeout khi sinh Audio (TTS)**:
   - Các API và client Axios được tăng giới hạn timeout lên **300 giây** để xử lý các đoạn văn bản dài tiếng Việt. Hãy đảm bảo TTS Agent (cổng `8104`) đang hoạt động bình thường.
3. **Đường dẫn tệp PDF/Audio không hoạt động**:
   - Tệp tĩnh được phục vụ qua FastAPI static files tại `/static/data/`. Đảm bảo file tồn tại trong thư mục `data/` tương ứng.
4. **Xung đột cổng kết nối (Port Conflicts)**:
   - Nếu các cổng `8000`, `8101`, `8102`, `8103`, `8104` hoặc `5173` bị chiếm dụng bởi các tiến trình chạy ngầm cũ, hãy chạy:
     ```cmd
     scripts\kill_project_ports.bat
     ```

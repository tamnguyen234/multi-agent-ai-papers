# Kịch bản Demo (Demo Script)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20  
> **Thời gian demo ước tính**: 10–15 phút  
> **Mode**: mock_fallback (demo nhanh, không cần GPU)

---

## Chuẩn bị trước khi demo

### Yêu cầu hệ thống
- Windows 10/11
- Python ≥ 3.10
- Node.js ≥ 18
- MySQL Server đang chạy (local hoặc Docker)
- Tất cả venv đã được setup (`scripts\setup_env.bat` đã chạy)

### Khởi động hệ thống (chạy trước 5 phút)

Mở **5 terminal** riêng biệt và chạy:

```cmd
# Terminal 1 – Backend Gateway
scripts\run_backend.bat

# Terminal 2 – Summarizer Agent
scripts\run_summarizer_agent.bat

# Terminal 3 – Trend Agent
scripts\run_trend_agent.bat

# Terminal 4 – Q&A Agent
scripts\run_qa_agent.bat

# Terminal 5 – TTS Agent
scripts\run_tts_agent.bat
```

Hoặc dùng script tự động:
```cmd
scripts\run_all.bat
```

Sau đó mở **Terminal 6** để khởi Frontend:
```cmd
cd frontend
npm run dev
```

Kiểm tra tất cả đã chạy:
```cmd
scripts\check_health.bat
```

Kết quả mong đợi:
```
[Backend]   ✓ http://127.0.0.1:8000/health → {"status":"ok"}
[Summarizer]✓ http://127.0.0.1:8101/health → {"status":"ok"}
[Trend]     ✓ http://127.0.0.1:8102/health → {"status":"ok"}
[Q&A]       ✓ http://127.0.0.1:8103/health → {"status":"ok"}
[TTS]       ✓ http://127.0.0.1:8104/health → {"status":"ok"}
[Frontend]  ✓ http://localhost:5173
```

---

## Kịch bản Demo

### Scene 1: Đăng ký & Đăng nhập (1-2 phút)

1. Mở trình duyệt tại `http://localhost:5173`
2. Nhấn **"Đăng ký"** trên màn hình login
3. Điền form đăng ký:
   - Username: `demo_user`
   - Email: `demo@ai-paper.com`
   - Password: `Demo@2024`
   - Full name: `Người dùng Demo`
4. Nhấn **Register** → Toast thành công "Đăng ký thành công!"
5. Tự động chuyển về trang Login → đăng nhập với tài khoản vừa tạo
6. **Điểm nhấn**: Hệ thống dùng JWT – token lưu trong localStorage, bảo mật cao

---

### Scene 2: Xem danh sách bài báo AI (2-3 phút)

1. Sau khi đăng nhập → tự động điều hướng về trang **Papers** (`/papers`)
2. Hiển thị danh sách các bài báo AI đã tổng hợp từ arXiv
3. Demo tính năng **tìm kiếm**: gõ "transformer" → danh sách lọc theo title và abstract
4. Demo **phân trang**: scroll hoặc dùng nút next page
5. **Điểm nhấn**: Dữ liệu thực từ Summarizer Agent → arXiv RSS

> **Tip**: Nếu danh sách trống, chạy seed data:  
> `curl -X POST http://127.0.0.1:8000/api/v1/dev/seed-papers`

---

### Scene 3: Xem chi tiết bài báo (2-3 phút)

1. Click vào một bài báo bất kỳ → mở trang **Paper Detail** (`/papers/:id`)
2. Hiển thị:
   - Tiêu đề, tác giả, ngày xuất bản
   - Abstract gốc
   - **Summary** được AI tóm tắt (highlight điểm này)
   - Nút **"Tải PDF"** (nếu PDF đã được download)
3. Demo **Audio Player**:
   - Nhấn nút nghe audio tóm tắt (nếu audio đã có)
   - **Điểm nhấn**: TTS Agent chuyển đổi summary thành giọng nói

---

### Scene 4: Hỏi đáp RAG với bài báo (3-4 phút)

1. Từ trang Paper Detail → nhấn **"Chat về bài báo"**
2. Hệ thống tạo phiên chat mới (`POST /chat/sessions`)
3. Nhập câu hỏi ví dụ:
   - "Phương pháp chính của bài báo này là gì?"
   - "Kết quả thí nghiệm quan trọng nhất là gì?"
   - "So sánh phương pháp này với BERT như thế nào?"
4. Hệ thống:
   - Gọi Q&A Agent → RAG query (hoặc mock)
   - Hiển thị câu trả lời của AI
   - Hiển thị **nguồn trích dẫn** (trang trong PDF)
5. Demo **TTS cho chat**: nhấn nút loa trên câu trả lời → phát audio
6. **Điểm nhấn**: Toàn bộ luồng Backend → Agent → DB → Frontend trong vài giây

---

### Scene 5: Dashboard Xu hướng chủ đề (2-3 phút)

1. Nhấn menu **"Xu hướng"** → trang Trend (`/trend`)
2. Hiển thị:
   - Biểu đồ phân phối chủ đề (danh sách cards)
   - Số bài báo mỗi chủ đề
   - Từ khóa đại diện mỗi topic
3. Nhấn vào topic card → xem danh sách bài báo thuộc topic đó
4. **Điểm nhấn**:
   - Trend Agent dùng BERTopic / rule-based để phân loại tự động
   - Cập nhật theo thời gian thực khi có bài mới

---

### Scene 6: Cài đặt tài khoản (1 phút)

1. Nhấn avatar/username → **"Profile"**
2. Hiển thị thông tin user
3. Demo toggle **"Nhận thông báo digest hàng ngày"**:
   - Toggle ON/OFF → Toast thành công
   - Nếu lỗi API → tự động rollback + Toast lỗi
4. **Điểm nhấn**: Hệ thống email tự động gửi digest 02:00 AM hàng ngày

---

### Scene 7: Kiến trúc kỹ thuật (Q&A với giảng viên)

Mở Swagger UI để demo API:
- `http://127.0.0.1:8000/docs`

Các câu hỏi thường gặp:

**Q: Tại sao dùng API Gateway thay vì gọi trực tiếp Agent?**  
A: Tập trung xác thực, logging, rate limiting. Frontend không cần biết địa chỉ Agent.

**Q: Database lưu gì, không lưu gì?**  
A: Chỉ lưu metadata (arxiv_id, paths, scores). PDF/Audio/FAISS nằm local trong `data/`.

**Q: Mock fallback khác real như thế nào?**  
A: Mock trả về dữ liệu cố định, không dùng AI thật. Đổi `SUMMARIZER_MODE=real` trong `.env` để kích hoạt.

**Q: Scheduler hoạt động thế nào?**  
A: APScheduler cron `0 2 * * *` (02:00 AM) tự động gọi Summarizer → tạo digest → gửi email.

---

## Kịch bản demo nâng cao (nếu có thời gian)

### Kích hoạt digest thủ công
```bash
curl -X POST http://127.0.0.1:8000/api/v1/digests/trigger
```

### Kích hoạt phân tích trend thủ công
```bash
curl -X POST http://127.0.0.1:8000/api/v1/trend/analyze
```

### Test pipeline đầy đủ
```cmd
scripts\test_full_pipeline.bat
```
Xem kết quả: 26/28 PASS, 2/28 WARN, 0 FAIL (từ Task 19).

---

## Lưu ý cho người demo

> [!IMPORTANT]
> - Đảm bảo tất cả 5 service đang chạy trước khi demo
> - Dùng URL `http://localhost:5173` (không dùng `127.0.0.1:5173`) cho Frontend
> - Database phải có ít nhất 5-10 bài báo (chạy seed nếu cần)

> [!TIP]
> - Chuẩn bị sẵn tab browser với trang Papers đã có dữ liệu
> - Chuẩn bị sẵn câu hỏi mẫu cho phần Chat demo
> - Demo Swagger UI song song để thấy API responses thực tế

---

*Tham khảo: [docs/deployment_notes.md](deployment_notes.md) | [docs/agent_workflow.md](agent_workflow.md)*

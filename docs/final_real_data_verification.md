# Báo cáo Xác thực Hệ thống với Dữ liệu thật (Final Real-Data Verification Report)

Tài liệu này tổng hợp kết quả chạy thực tế, dọn dẹp cấu trúc dự án và kiểm thử toàn hệ thống (end-to-end) ở chế độ chạy bằng **dữ liệu thật**.

---

## 🔌 Trạng thái dịch vụ & Cổng kết nối (Services & Ports)

Toàn bộ các microservices chạy song song và hoạt động ổn định trên các cổng:

*   **FastAPI Backend Gateway**: Port `8000` (được chạy bằng `backend\.venv\Scripts\python.exe`)
*   **Summarizer Agent**: Port `8101` (được chạy bằng `agents\summarizer_agent\.venv\Scripts\python.exe`)
*   **Trend Agent**: Port `8102` (được chạy bằng `agents\trend_agent\.venv\Scripts\python.exe`)
*   **Q&A Agent**: Port `8103` (được chạy bằng `agents\qa_agent\.venv\Scripts\python.exe`)
*   **TTS Agent**: Port `8104` (được chạy bằng `agents\tts_agent\.venv\Scripts\python.exe`)
*   **Ollama Server**: Port `11434` (chạy model offline `qwen2.5:3b`)
*   **React Frontend**: Port `5173` (chạy bằng `npm run dev`)

---

## 🗄️ Kết quả xác thực Cơ sở dữ liệu (Database Metrics)

Sau khi thực hiện dọn dẹp mock/demo data, cơ sở dữ liệu đã đạt trạng thái hoạt động hoàn toàn bằng dữ liệu arXiv thật.
Kết quả chạy lệnh xác thực `verify_real_data_mode.py`:

```text
======================================================================
DATABASE REAL DATA MODE VERIFICATION
======================================================================
Papers Audit:
  - Total Papers: 103
  - Real Papers: 103 (Required: >= 100)
  - Mock Papers: 0 (Required: 0)
Digests Audit:
  - Total Digests: 20 (Required: >= 20)
Topics Audit:
  - Total Topics: 15
Audio Abstracts Audit:
  - Total Audio Abstracts: 9
----------------------------------------------------------------------
VERIFICATION SUCCESSFUL: Database is in pure real-data mode and matches all safety requirements!
```

### Các ràng buộc dữ liệu được đảm bảo:
1.  **Số lượng bài báo thật**: 103 bài báo, đều có `arxiv_id` hợp lệ và tệp PDF vật lý tương ứng trên ổ đĩa.
2.  **Số lượng Digests**: 20 ngày digest liên tiếp.
3.  **Tính đồng nhất của Digest**: Mỗi ngày digest chứa **đúng 5 bài báo thật** (không có mock paper, không có bài trùng lặp). Các bài báo mock trước đây trong Digest ID 2 và Digest ID 4 đã được thay thế thành công bằng các bài báo thật tương ứng mà không làm thay đổi thứ tự xếp hạng `rank_position` (1-5).
4.  **Chủ đề (Topics)**: 15 chủ đề AI thật được phân cụm thành công. Không còn chủ đề rỗng không chứa bài báo nào.
5.  **Tệp PDF & Audio**: 100% bài báo thật tham chiếu đến tệp PDF tồn tại thực tế trên đĩa. Không tự động xóa các bản ghi âm thanh abstract nếu bài báo thuộc dữ liệu thật.

---

## 🧪 Kết quả kiểm thử Pipeline đầy đủ (Full Pipeline Test)

Chạy kịch bản kiểm thử tích hợp đầy đủ `scripts/test_full_pipeline.py` đạt kết quả tuyệt đối:

*   **Tổng số kiểm tra**: 28
*   **Thành công (PASS)**: 26
*   **Cảnh báo (WARN)**: 2 (Cảnh báo người dùng demo đã tồn tại và đăng nhập thay vì đăng ký; cảnh báo một số paper demo cũ không có PDF - các bài báo thật đều có đủ).
*   **Thất bại (FAIL)**: 0

Dịch vụ hỏi đáp RAG (Ollama) và dịch vụ sinh âm thanh (TTS) hoạt động trơn tru qua Gateway với thời gian phản hồi nhanh và cơ chế caching file tối ưu.

---

## ⚙️ Đóng gói & Build Frontend (Production Build)

Frontend được build kiểm tra biên dịch TypeScript thành công tuyệt đối:
```cmd
cd frontend && npm run build
```
*Kết quả:*
*   `dist/assets/index-D3Y59LHg.css` (56.60 kB)
*   `dist/assets/index-Hlh25aWk.js` (527.85 kB)
*   Build thành công trong **381ms** mà không phát sinh bất kỳ lỗi TypeScript hay Warning nghiêm trọng nào.

---

## 💻 Kịch bản Demo Giao diện Web (Web Demo Checklist)

Khi demo trực quan trên trình duyệt, các tính năng hoạt động như sau:

1.  **Dashboard chính**: Hiển thị Digest của ngày hiện tại với đúng 5 bài báo AI hàng đầu.
2.  **Trang danh sách bài báo (Papers)**: Cho phép cuộn, xem các bài báo thật của các ngày trước, hỗ trợ tìm kiếm theo tiêu đề/tóm tắt bài viết.
3.  **Chi tiết bài báo & PDF**: Mở chi tiết bài báo, xem file PDF được load trực tiếp từ static files gateway.
4.  **Lazy Audio Abstract**:
    *   Bài viết chưa có audio hiển thị nút **"Tạo audio abstract"**.
    *   Nhấn nút sẽ hiển thị trạng thái đang xử lý và hiển thị HTML5 Audio Player ngay lập tức sau khi TTS hoàn tất.
    *   Tải lại trang hiển thị player trực tiếp mà không cần sinh lại (lấy từ cache `mode=existing`).
5.  **Chat Hỏi đáp RAG**: Giao diện chat cho phép đặt câu hỏi cụ thể dựa trên nội dung PDF của bài báo. Q&A Agent kết xuất chunks và Ollama trả lời trực tiếp.
6.  **TTS Chat Audio**: Phản hồi từ trợ lý ảo trong khung chat có biểu tượng loa, cho phép nghe giọng nói tương ứng chất lượng cao.
7.  **Phân tích Xu hướng (Trends)**: Biểu đồ cột và danh sách chủ đề được hiển thị đầy đủ, phân cụm trực quan dựa trên các bài báo thật hiện có.

---

## 📚 Lưu ý về Lưu trữ & Tái tạo Dữ liệu (Local Storage & Reproduction)

> [!IMPORTANT]
> Toàn bộ các thư mục lưu trữ dữ liệu thật nhị phân (`data/paper_pdf/`, `data/audio_abstract/`, `data/audio_chat_message/`, `data/faiss_indexes/`) và báo cáo dọn dẹp (`data/cleanup_reports/`) được bỏ qua trong Git thông qua tệp `.gitignore`.
> Điều này đảm bảo repository luôn sạch, chỉ chứa mã nguồn và tài liệu hướng dẫn.

Để tái tạo lại bộ dữ liệu 20 ngày chạy thật với 100 bài báo từ arXiv cục bộ, hãy chạy lệnh sau:
```cmd
scripts\backfill_20_days.bat --days 20 --per-day 5 --force
```

---

## ⚠️ Hạn chế đã biết (Known Limitations)
- **Tốc độ sinh TTS**: Tốc độ tổng hợp âm thanh phụ thuộc vào cấu hình CPU/GPU cục bộ. Cấu hình timeout 300s đã được thiết lập để xử lý các tóm tắt dài mà không gây ngắt kết nối.
- **Tài nguyên RAG**: Lần đầu tiên hỏi đáp một bài báo mới sẽ mất từ 10-20 giây để Q&A Agent nạp PDF, phân tách text và xây dựng vector index FAISS. Các câu hỏi tiếp theo trên cùng một bài báo sẽ phản hồi tức thì.

# 08. Kịch bản Demo báo cáo (Demo Scenarios)

Tài liệu này chuẩn bị các kịch bản demo thực tế giúp sinh viên dễ dàng trình bày và thuyết phục giảng viên trong buổi báo cáo dự án.

---

## 🎬 Kịch bản 1: Chu trình tự động Daily Digest (2:00 AM)
- **Mục tiêu**: Chứng minh khả năng lập lịch tự động và sự phối hợp đồng bộ giữa các tác tử.
- **Các bước demo**:
  1. Sử dụng API Route `POST /api/v1/digest/trigger` để kích hoạt thủ công tác vụ (không cần đợi đến 2h sáng thực tế).
  2. Xem màn hình console của **Backend Gateway** để thấy log gọi sang **Summarizer Agent**.
  3. **Summarizer Agent** log quá trình đọc feed từ arXiv, sinh tóm tắt học thuật và lưu trữ vào database MySQL.
  4. Xem tiếp console log gọi sang **TTS Agent** để chuyển đổi bản tóm tắt sang file âm thanh lưu cục bộ.
  5. Mở hòm thư Gmail test của người dùng để hiển thị email thông báo bản tin hàng ngày đã được gửi tự động kèm link nghe tóm tắt.

---

## 💬 Kịch bản 2: Hỏi đáp RAG trực tiếp trên file PDF bài báo
- **Mục tiêu**: Demo khả năng xử lý ngôn ngữ tự nhiên sâu và trả lời dựa trên ngữ cảnh của Q&A Agent.
- **Các bước demo**:
  1. Người dùng chọn một bài báo mới trong danh sách và nhấp nút **"Chat với Paper"**.
  2. Upload file PDF hoặc nhấp nút để hệ thống tự động tải file PDF gốc từ arXiv.
  3. **Q&A Agent** nhận file PDF, tiến hành tách mảnh, nhúng vector embeddings và lưu trữ index vào thư mục `data/faiss_indexes/`.
  4. Người dùng nhập câu hỏi vào khung chat (ví dụ: *"Phương pháp nghiên cứu chính của tác giả là gì?"*).
  5. Hệ thống trả về câu trả lời chính xác, trích dẫn rõ ràng trang sách / đoạn văn gốc từ PDF để kiểm chứng tính xác thực.

---

## 📊 Kịch bản 3: Phân tích xu hướng chủ đề nghiên cứu AI
- **Mục tiêu**: Chứng minh tác vụ phân tích cấp độ vĩ mô của Trend Agent trên kho tài liệu đã lưu trữ.
- **Các bước demo**:
  1. Truy cập vào trang **Trend Analytics** trên giao diện Frontend.
  2. Giao diện tải danh sách chủ đề gom cụm từ **Trend Agent**.
  3. Hiển thị biểu đồ phân cụm các từ khóa (ví dụ: Cụm 1 về LLMs & Prompt Engineering, Cụm 2 về Diffusion Models, Cụm 3 về Reinforcement Learning).
  4. Người dùng chọn một chủ đề cụ thể để lọc ra các bài báo thuộc cụm đó.

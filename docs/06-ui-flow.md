# 06. Luồng giao diện người dùng (UI Flow)

Giao diện người dùng được xây dựng tối giản, trực quan và tập trung vào trải nghiệm đọc/nghe tin tức bài báo AI.

---

## 🗺️ Bản đồ chuyển trang (Navigation Map)

```text
  [Login Page] ----(Thành công)----> [Dashboard (Trang chủ)]
                                         |
         +-------------------------------+------------------------------+
         |                               |                              |
         v                               v                              v
  [Detail Paper Summary]        [Chat RAG Workspace]        [Trend Visualization]
     |                                   ^
     +---(Nhấp "Chat with Paper")--------+
```

---

## 📱 Chi tiết các Trang/Giao diện chính

### 1. Trang đăng nhập / Đăng ký (Auth Page)
- **Mô tả**: Giao diện đăng nhập để bảo mật thông tin hội thoại chat RAG của từng người dùng.
- **Tính năng**: Form điền email/mật khẩu, chuyển hướng nhanh sang trang Đăng ký tài khoản mới.

### 2. Trang chủ Dashboard (Paper Feed)
- **Mô tả**: Hiển thị danh sách các bài báo AI thu thập hàng ngày.
- **Tính năng**:
  - Grid card hiển thị tiêu đề, tác giả, và ngày phát hành bài báo.
  - Bộ lọc bài báo theo từ khóa / xu hướng.
  - Nút phát nhanh (Quick Play) tóm tắt âm thanh (Audio) trực tiếp trên trang chủ.

### 3. Trang chi tiết bài báo (Paper Detail)
- **Mô tả**: Xem tóm tắt chi tiết do Agent sinh ra.
- **Tính năng**:
  - Trình đọc Markdown hiển thị cấu trúc bản tóm tắt (Mục tiêu nghiên cứu, Phương pháp, Kết quả).
  - Trình phát nhạc (Audio Player) cho phép tua, tăng tốc độ phát tóm tắt nói.
  - Nút "Tải file PDF gốc" và nút "Hỏi đáp AI" để chuyển nhanh sang khu vực chat RAG.

### 4. Không gian hỏi đáp RAG (Chat RAG Workspace)
- **Mô tả**: Giao diện hội thoại chia đôi màn hình.
- **Tính năng**:
  - Bên trái: Hiển thị trình xem tài liệu PDF gốc (`iframe` hoặc thư viện PDF Viewer).
  - Bên phải: Khung chatbox với tin nhắn của người dùng và phản hồi của RAG Agent.
  - Hỗ trợ phát Audio câu trả lời của Agent trực tiếp bằng giọng đọc (TTS).

### 5. Bảng điều khiển xu hướng (Trend Analytics Dashboard)
- **Mô tả**: Biểu diễn bản đồ trực quan các chủ đề AI đang thu hút nhiều sự quan tâm.
- **Tính năng**:
  - Sơ đồ bong bóng (Bubble Chart) hoặc bản đồ cụm (Scatter Plot) mô tả các Topic clusters từ Trend Agent.
  - Danh sách top từ khóa xu hướng trong tuần.

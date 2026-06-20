# 02. Kiến trúc hệ thống (System Architecture)

## 🏗️ Kiến trúc tổng thể
Hệ thống được thiết kế theo kiến trúc **API Gateway & Microservices**. 
Backend chính đóng vai trò điều phối (Gateway), xác thực người dùng, lập lịch tác vụ và lưu trữ trạng thái. Các Agent hoạt động độc lập dưới dạng các service API riêng biệt.

## 🛠️ Các thành phần chính
1. **Frontend (React + Vite)**:
   - Giao diện Single Page Application (SPA).
   - Tương tác thời gian thực với chat box.
   - Trình phát âm thanh (Audio Player) tích hợp.
   
2. **Backend Gateway (FastAPI)**:
   - Quản lý cơ sở dữ liệu quan hệ (MySQL).
   - Cung cấp các APIs bảo mật (JWT Authentication).
   - APScheduler chạy ngầm quản lý chu trình daily digest.
   
3. **Data Storage & Vector Store**:
   - Lưu trữ vật lý file PDF bài báo và file Audio MP3 tại thư mục `./data/`.
   - Cơ sở dữ liệu Vector `FAISS` dùng để tìm kiếm ngữ cảnh cho RAG.
   
4. **Hệ thống AI Agents**:
   - Giao tiếp qua giao thức HTTP RESTful API.
   - Có thể mở rộng (scale) độc lập tùy theo tải xử lý của từng tác vụ AI.

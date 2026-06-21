# 01. Giới thiệu dự án (Introduction)

## 📌 Tổng quan hệ thống
Hệ thống **Quản lý Hệ thống Multi-Agent tương tác Bài báo AI** là một giải pháp tự động hóa thông minh nhằm giúp các nghiên cứu viên, lập trình viên và người đam mê AI dễ dàng cập nhật kiến thức học thuật từ kho tàng khổng lồ của arXiv mà không bị quá tải thông tin.

## ⚠️ Vấn đề giải quyết
1. **Quá tải thông tin**: Mỗi ngày có hàng trăm bài báo AI được xuất bản trên arXiv. Nghiên cứu viên không thể đọc hết.
2. **Khó tiếp cận nội dung dài**: Nhiều bài báo dài từ 10-30 trang. Cần một bản tóm tắt nhanh, chuẩn học thuật để biết có nên đọc sâu hay không.
3. **Thiếu khả năng tương tác trực tiếp**: Đọc PDF truyền thống là một chiều. Người dùng muốn được hỏi đáp, giải thích các thuật ngữ khó trực tiếp trên nội dung bài báo.
4. **Tiện ích đa phương tiện**: Hỗ trợ chuyển đổi tóm tắt học thuật thành Audio chất lượng cao để nghe lúc di chuyển (như podcast).

## 🤖 Giải pháp Multi-Agent
Hệ thống sử dụng mô hình đa tác tử (Multi-Agent System) phối hợp thực hiện tác vụ:
- **Summarizer Agent**: Tự động thu thập bài báo AI nổi bật trên arXiv hàng ngày và thực hiện tóm tắt.
- **Trend Agent**: Gom cụm các từ khóa và nội dung bài báo để phát hiện ra xu hướng nghiên cứu mới nhất.
- **Q&A Agent**: Hỗ trợ hội thoại RAG (Retrieval-Augmented Generation) trực tiếp trên file PDF của bài báo.
- **TTS Agent**: Chuyển đổi văn bản phản hồi và tóm tắt thành âm thanh tiếng Việt/Anh sống động.

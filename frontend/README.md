# AI Paper Multi-Agent Frontend

Giao diện người dùng của hệ thống **AI Paper Multi-Agent System**, được xây dựng trên nền tảng **React (Typescript)** và công cụ build **Vite**.

---

## 🔌 Cổng kết nối (Port)
- Cổng mặc định của Vite: `5173` (URL: `http://localhost:5173`)

---

## 🚀 Hướng dẫn khởi chạy

*Lưu ý: Tại bước Task 1, dự án mới chỉ cấu hình cấu trúc thư mục tĩnh.*

### 1. Khởi tạo dự án và cài đặt
```bash
cd frontend
npm install
```

### 2. Cấu hình `.env`
Sao chép `.env.example` thành `.env` và cập nhật cổng API Gateway:
```bash
cp .env.example .env
```

### 3. Chạy môi trường Development
```bash
npm run dev
```

---

## 📁 Cấu trúc thư mục Frontend
- `/src/pages`: Giao diện các trang chính (Home, Login, Register, PaperDetail, Chat, Trend Dashboard).
- `/src/components`: Các component UI dùng chung (Button, Card, AudioPlayer, Navbar, ChatBox).
- `/src/services`: Lớp gọi API kết nối đến Backend Gateway.
- `/src/routes`: Quản lý đường dẫn định tuyến (react-router-dom).
- `/src/hooks`: Custom hooks dùng chung (useAuth, useFetch).
- `/src/layouts`: Khung bao quanh giao diện (MainLayout, AuthLayout).

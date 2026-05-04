# Tóm tắt hệ thống Đồ án tốt nghiệp

Hệ thống được xây dựng nhằm mục đích giám sát và phân tích hành vi sinh viên trong lớp học sử dụng Trí tuệ nhân tạo (Computer Vision).

## 1. Chức năng và Các file mã nguồn tương ứng

### A. Quản lý Người dùng & Xác thực
*   **Đăng ký/Đăng nhập**: Cho phép giảng viên/quản trị viên truy cập hệ thống.
    *   *Frontend*: `frontend/pages/login.py`, `frontend/pages/register.py`
    *   *Backend*: `backend/api/router/user_router.py`, `backend/core/auth.py`
*   **Quản lý Tài khoản**: Chỉnh sửa thông tin cá nhân, phân quyền Admin.
    *   *Frontend*: `frontend/pages/setting.py`
    *   *Backend*: `backend/utils/create_admin.py` (Script khởi tạo)

### B. Giám sát Thời gian thực (Real-time Monitoring)
*   **Stream Video & Nhận diện**: Kết nối Camera, nhận diện sinh viên, trạng thái tập trung (focused) hoặc buồn ngủ (sleeping).
    *   *Frontend*: `frontend/pages/home.py`
    *   *Backend*: `backend/api/router/camera_router.py`, `backend/ai_model/` (Logic YOLOv8)

### C. Quản lý Lịch sử & Phân tích Session
*   **Danh sách buổi học**: Xem lại các phiên giám sát đã thực hiện.
    *   *Frontend*: `frontend/pages/history.py`
    *   *Backend*: `backend/api/router/history_router.py`
*   **Chi tiết & Phân tích**: Biểu đồ diễn biến sự tập trung theo thời gian trong một buổi học.
    *   *Frontend*: `frontend/pages/session_analysis.py`, `frontend/pages/session_detail.py`
    *   *Backend*: `backend/api/router/ai_result_router.py`

### D. Chi tiết Khung hình (Frame Details)
*   **Truy xuất Frame**: Xem chi tiết từng ảnh cắt từ video và kết quả AI tại thời điểm đó.
    *   *Frontend*: `frontend/pages/frame_detail.py`
    *   *Backend*: `backend/api/router/frame_router.py`, `backend/service/frame_service.py`

### E. Thống kê Tổng quan (Dashboard Statistics)
*   **Biểu đồ tổng hợp**: Thống kê hiệu quả học tập theo ngày/tuần/tháng.
    *   *Frontend*: `frontend/pages/statistics.py`
    *   *Backend*: `backend/api/router/statistics_router.py`

---

## 2. Cơ chế Bảo mật của Hệ thống

Hệ thống áp dụng các tiêu chuẩn bảo mật hiện đại để bảo vệ dữ liệu:

1.  **Xác thực JWT (JSON Web Tokens)**:
    *   Sử dụng Access Token và Refresh Token để duy trì phiên đăng nhập an toàn.
    *   Token được lưu trữ trong HttpOnly Cookies để chống tấn công XSS (Cross-Site Scripting).
    *   File thực hiện: `backend/core/auth.py`, `backend/core/security.py`.
2.  **Mã hóa mật khẩu**:
    *   Mật khẩu được băm (hashing) bằng thuật toán **Bcrypt** trước khi lưu vào cơ sở dữ liệu. Không lưu mật khẩu dạng văn bản thuần túy.
    *   File thực hiện: `backend/core/security.py`.
3.  **Kiểm soát truy cập (Middleware & Dependencies)**:
    *   Mọi yêu cầu API (trừ login/register) đều yêu cầu token hợp lệ.
    *   Cơ chế **Token Blacklisting** cho phép vô hiệu hóa token khi người dùng đăng xuất.
    *   File thực hiện: `backend/core/dependencies.py`, `backend/core/token_blacklist.py`.
4.  **Giới hạn tốc độ (Rate Limiting)**:
    *   Ngăn chặn các cuộc tấn công Brute-force hoặc Spam API.
    *   File thực hiện: `backend/core/rate_limiter.py`.
5.  **Cấu hình Môi trường**:
    *   Thông tin nhạy cảm (Secret Key, DB URL) được quản lý qua file `.env`, không hardcode trong mã nguồn.

---

## 3. Thông tin chuẩn bị cho buổi Thuyết trình

Để buổi thuyết trình ấn tượng, bạn nên chuẩn bị kỹ các nội dung sau:

### Tóm tắt Công nghệ (Tech Stack)
*   **Backend**: FastAPI (Python) - Hiệu năng cao, hỗ trợ Asynchronous.
*   **Frontend**: Streamlit - Xây dựng Dashboard dữ liệu nhanh và trực quan.
*   **AI Model**: YOLOv8 (You Only Look Once) - Tốc độ nhận diện nhanh nhất hiện nay cho bài toán thời gian thực.
*   **Database**: PostgreSQL (hoặc SQLite tùy cấu hình) với SQLAlchemy ORM.
*   **Deployment**: Docker & Docker Compose - Giúp triển khai hệ thống nhất quán trên mọi môi trường.

### Các "Key Selling Points" (Điểm nhấn)
1.  **Tính thực tiễn**: Giải quyết vấn đề quản lý chất lượng dạy và học tự động.
2.  **Độ trễ thấp**: Tối ưu hóa luồng Stream và xử lý AI để đạt FPS ổn định.
3.  **Dashboard trực quan**: Không chỉ nhận diện mà còn chuyển hóa thành biểu đồ xu hướng (Analytics), giúp giảng viên có cái nhìn tổng thể.
4.  **Kiến trúc sạch (Clean Architecture)**: Phân tách rõ ràng giữa Service, Router, và CRUD giúp dễ dàng bảo trì và mở rộng (ví dụ: thêm loại nhận diện hành vi mới).

### Câu hỏi Hội đồng có thể hỏi
*   *Làm sao để đảm bảo quyền riêng tư của sinh viên?* (Trả lời: Dữ liệu hình ảnh có thể được xóa sau khi xử lý, chỉ lưu kết quả thống kê).
*   *Hệ thống xử lý thế nào khi lớp học đông sinh viên?* (Trả lời: YOLOv8 có khả năng nhận diện đa đối tượng tốt, có thể nâng cấp phần cứng GPU để tăng tốc độ).
*   *Tại sao chọn FastAPI thay vì Django/Flask?* (Trả lời: FastAPI nhanh hơn, hỗ trợ type hinting tốt hơn và tự động tạo tài liệu API Swagger).

---
*Chúc bạn có một buổi thuyết trình thành công rực rỡ!*

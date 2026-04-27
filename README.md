# 🎓 EduVision AI — Hệ thống Giám sát Lớp học bằng Trí tuệ Nhân tạo

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.55-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00B4D8?logo=pytorch&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**Hệ thống phát hiện trạng thái học sinh trong lớp học theo thời gian thực,  
sử dụng camera, AI nhận diện khuôn mặt, và dashboard quản lý trực quan.**

[📖 Tính năng](#-tính-năng) · [🏗️ Kiến trúc](#️-kiến-trúc-hệ-thống) · [🚀 Cài đặt](#-cài-đặt-và-chạy) · [📡 API](#-api-endpoints) · [📸 Giao diện](#-giao-diện)

</div>

---

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Kiến trúc hệ thống](#️-kiến-trúc-hệ-thống)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Tech Stack](#-tech-stack)
- [Cài đặt và chạy](#-cài-đặt-và-chạy)
- [Cấu hình môi trường](#-cấu-hình-môi-trường)
- [API Endpoints](#-api-endpoints)
- [Bảo mật](#-bảo-mật)
- [Giao diện](#-giao-diện)
- [Hướng dẫn phát triển](#-hướng-dẫn-phát-triển)

---

## 🎯 Giới thiệu

**EduVision AI** là đề tài đồ án tốt nghiệp xây dựng hệ thống giám sát lớp học thông minh. Hệ thống sử dụng camera để chụp ảnh lớp học theo chu kỳ 30 giây, sau đó áp dụng mô hình AI (YOLOv8 + Deep Learning) để phát hiện học sinh đang **tập trung** hay **buồn ngủ**. Kết quả được hiển thị trực tiếp trên dashboard web cho giảng viên.

### Mục tiêu

- ✅ Hỗ trợ giảng viên theo dõi sự chú ý của học sinh trong thời gian thực
- ✅ Lưu lịch sử phiên học để phân tích xu hướng
- ✅ Cung cấp thống kê trực quan theo ngày/tuần
- ✅ Cho phép chỉnh sửa thủ công kết quả nhận diện AI

---

## ✨ Tính năng

### 🔴 Giám sát thời gian thực
- Kết nối camera (webcam hoặc camera USB) và phát MJPEG stream
- Trích xuất khung hình mỗi 30 giây tự động
- Phát hiện khuôn mặt và phân loại trạng thái: **Tập trung / Buồn ngủ**
- Hiển thị bounding box tương tác trên ảnh chụp

### 📊 Dashboard phân tích
- **Trang chủ**: Feed camera trực tiếp + danh sách khung hình mới nhất
- **Phân tích phiên**: Grid hiển thị tất cả khung hình của phiên học hiện tại
- **Chi tiết phiên**: Biểu đồ tròn phân bổ hành vi + bảng khung hình theo phân trang
- **Chi tiết khung hình**: Ảnh tương tác có bounding box, click để thay đổi nhãn
- **Lịch sử**: Danh sách tất cả phiên học, tìm kiếm, phân trang, xóa phiên
- **Thống kê**: Biểu đồ xu hướng buồn ngủ theo 7 ngày, KPI cards

### 🔐 Xác thực & Bảo mật
- JWT Authentication với Access Token (1 giờ) + Refresh Token (7 ngày)
- Rate Limiting: 5 lần/15 phút/IP cho login và register
- Token Blacklist khi logout
- Bcrypt password hashing
- CORS theo environment (dev/prod)

### 👤 Quản lý tài khoản
- Đăng ký / Đăng nhập / Đăng xuất
- Chỉnh sửa thông tin hồ sơ
- Đổi mật khẩu

---

## 🏗️ Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                   │
│                                                          │
│  pages/          services/          utils/               │
│  ├─ home.py      ├─ auth_api.py     ├─ auth_guard.py     │
│  ├─ history.py   ├─ frame_api.py    ├─ http.py           │
│  ├─ statistics.py├─ history_api.py  ├─ load_css.py       │
│  ├─ login.py     ├─ stats_api.py    └─ ...               │
│  └─ ...          └─ user_api.py                          │
│                                                          │
│  components/     styles/                                  │
│  └─ app_sidebar  └─ *.css (per page)                     │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTP/REST (requests.Session + JWT)
                   ▼
┌──────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                      │
│                                                          │
│  api/router/     service/           crud/                │
│  ├─ user         ├─ camera_service  ├─ user_crud         │
│  ├─ camera       └─ (AI pipeline)   ├─ session_crud      │
│  ├─ frame                           ├─ frame_crud        │
│  ├─ history      core/              └─ ai_result_crud    │
│  ├─ statistics   ├─ auth.py (JWT)                        │
│  └─ ai_result    ├─ security.py                          │
│                  ├─ dependencies.py                      │
│                  ├─ rate_limiter.py                      │
│  ai_model/       └─ token_blacklist.py                   │
│  └─ ai_pipeline.py (YOLOv8 + Model)                      │
└──────────────────┬───────────────────────────────────────┘
                   │ SQLAlchemy ORM
                   ▼
┌──────────────────────────────────────────────────────────┐
│                 PostgreSQL Database                       │
│                                                          │
│  Users → Sessions → Frames → AIResults → Statistics      │
└──────────────────────────────────────────────────────────┘
```

### Luồng xử lý chính

```
Camera → capture frame (30s interval)
       → YOLOv8 detect faces
       → Deep Learning model classify (Focus/Sleeping)
       → Save frame + bounding boxes to DB
       → Frontend fetches + displays results
```

---

## 📁 Cấu trúc thư mục

```
final_year_project/
├── 📄 .gitignore
├── 📄 requirements.txt           # Full dependency list
│
├── 🖥️  frontend/                 # Streamlit web app
│   ├── app.py                    # Entry point
│   ├── config.py                 # API_BASE_URL, COOKIE_PASSWORD
│   │
│   ├── pages/                    # One file = one page
│   │   ├── home.py               # Real-time monitoring
│   │   ├── session_analysis.py   # Current session frame grid
│   │   ├── session_detail.py     # Session KPI + frame table
│   │   ├── frame_detail.py       # Interactive bbox editing
│   │   ├── history.py            # Session history list
│   │   ├── statistics.py         # Daily trend charts
│   │   ├── setting.py            # Profile + password
│   │   ├── login.py              # Authentication
│   │   └── register.py           # Registration
│   │
│   ├── services/                 # API call layer (separated from UI)
│   │   ├── auth_api.py           # login, register, logout, refresh
│   │   ├── frame_api.py          # frames, frame detail, analysis
│   │   ├── history_api.py        # sessions, summary, detail, delete
│   │   ├── stats_api.py          # daily statistics
│   │   └── user_api.py           # profile, update, change password
│   │
│   ├── components/
│   │   └── app_sidebar.py        # Shared sidebar navigation
│   │
│   ├── utils/
│   │   ├── auth_guard.py         # require_auth() decorator
│   │   ├── http.py               # Session init, auth headers, safe_get/post
│   │   ├── load_css.py           # CSS file loader
│   │   └── hide_streamlit_sidebar.py
│   │
│   └── styles/                   # Per-page CSS files
│       ├── global.css
│       ├── sidebar.css
│       ├── home.css
│       ├── login.css
│       ├── register.css
│       ├── history.css
│       ├── session_analysis.css
│       ├── session_detail.css
│       ├── frame_detail.css
│       ├── setting.css
│       └── statistics.css
│
└── ⚙️  backend/                  # FastAPI application
    ├── main.py                   # App entry point, CORS, router registration
    ├── requirements.txt          # Backend-specific deps
    ├── .env                      # Environment variables (NOT committed)
    │
    ├── api/router/               # HTTP route handlers
    │   ├── user_router.py        # /users/*
    │   ├── camera_router.py      # /camera/*
    │   ├── frame_router.py       # /frames/*
    │   ├── history_router.py     # /history/*
    │   ├── statistics_router.py  # /stats/*
    │   └── ai_result_router.py   # /ai-result/*
    ├── service/
    │   └── camera_service.py     # Camera control + AI inference loop
    │
    ├── ai_model/
    │   ├── weights/              # Thư mục chứa trọng số mô hình
    │   │   ├── yolov8n.pt        # YOLOv8 weights (Committed)
    │   │   └── behavior_model_final.keras # CNN weights (Committed)
    │
    ├── crud/                     # Database operations
    │   ├── user_crud.py
    │   ├── session_crud.py
    │   ├── frame_crud.py
    │   ├── ai_result_crud.py
    │   └── statistics_crud.py
    │
    ├── models/                   # SQLAlchemy ORM models
    │   ├── user.py
    │   ├── session.py
    │   ├── frame.py
    │   ├── ai_result.py
    │   └── statistics.py
    │
    ├── schemas/                  # Pydantic request/response schemas
    ├── core/                     # Auth, security, rate limiting
    │   ├── auth.py               # JWT creation & verification
    │   ├── security.py           # Bcrypt, cookie settings
    │   ├── dependencies.py       # get_current_user(), get_client_ip()
    │   ├── rate_limiter.py       # In-memory rate limiting
    │   ├── token_blacklist.py    # Logout token revocation
    │   └── config.py             # Settings from .env
    │
    ├── database/
    │   └── database.py           # SQLAlchemy engine + session factory
    │
    └── tests/
        └── test_security.py      # Auth & rate limiting tests
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Mục đích |
|---|---|---|---|
| **Frontend** | Streamlit | 1.55 | Web UI framework |
| **Frontend** | streamlit-autorefresh | 1.0.1 | Auto-refresh polling |
| **Frontend** | streamlit-cookies-manager | 0.2.0 | JWT cookie persistence |
| **Frontend** | Plotly | 6.6 | Interactive charts |
| **Frontend** | Pandas | 2.3 | Data manipulation |
| **Backend** | FastAPI | 0.135 | REST API framework |
| **Backend** | Uvicorn | 0.41 | ASGI server |
| **Backend** | SQLAlchemy | 2.0 | ORM |
| **Backend** | Pydantic | 2.12 | Data validation |
| **Auth** | python-jose | 3.5 | JWT tokens |
| **Auth** | Bcrypt | 4.0 | Password hashing |
| **AI** | Ultralytics (YOLOv8) | 8.4 | Face/body detection |
| **AI** | PyTorch | 2.11 | Deep learning inference |
| **AI** | OpenCV | 4.13 | Camera capture & image processing |
| **AI** | Pillow | 12.1 | Image I/O |
| **Database** | PostgreSQL | 16 | Primary database |
| **Database** | psycopg2-binary | 2.9 | PostgreSQL adapter |

---

## 🚀 Cài đặt và chạy

### Yêu cầu hệ thống

- Python **3.11+** (tested on 3.13)
- PostgreSQL **14+**
- Webcam hoặc USB camera
- RAM: tối thiểu **4GB** (8GB khuyến nghị cho inference AI)

---

### Bước 1: Clone repository

```bash
git clone https://github.com/<your-username>/final_year_project.git
cd final_year_project
```

### Bước 2: Tạo virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
# Cài tất cả dependencies (cả frontend và backend)
pip install -r requirements.txt
```

> **Lưu ý Windows**: Một số thư viện camera (`pygrabber`, `pywin32`) chỉ hoạt động trên Windows. Trên Linux/macOS, OpenCV sẽ được dùng thay thế.

---

### Bước 4: Cấu hình PostgreSQL

```sql
-- Tạo database
CREATE DATABASE eduvision_db;
CREATE USER eduvision_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE eduvision_db TO eduvision_user;
```

### Bước 5: Tạo file `.env` cho Backend

Tạo file `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://eduvision_user:your_password@localhost/eduvision_db

# JWT Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long

# Environment
ENVIRONMENT=development        # hoặc production

# CORS (chỉ cần thiết cho production)
ALLOWED_ORIGINS=http://localhost:8501

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

> ⚠️ **Không commit file `.env`** — đã được thêm vào `.gitignore`

### Bước 6: Chạy Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ tự động tạo các bảng trong PostgreSQL khi khởi động lần đầu.

Kiểm tra backend hoạt động:
```
http://localhost:8000/health
http://localhost:8000/docs    ← Swagger UI
```

### Bước 7: Cấu hình Frontend

Tạo hoặc chỉnh sửa `frontend/config.py`:

```python
# Trỏ đến backend đang chạy
API_BASE_URL = "http://localhost:8000"
COOKIE_PASSWORD = "your-cookie-encryption-password"
```

### Bước 8: Chạy Frontend

```bash
cd frontend
streamlit run app.py
```

Frontend sẽ chạy tại: `http://localhost:8501`

---

### Chạy song song (khuyến nghị dùng 2 terminal)

```bash
# Terminal 1 — Backend
cd final_year_project/backend
uvicorn main:app --reload

# Terminal 2 — Frontend
cd final_year_project/frontend
streamlit run app.py
```

---

## ⚙️ Cấu hình môi trường

### Backend `backend/.env`

| Biến | Bắt buộc | Mặc định | Mô tả |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `SECRET_KEY` | ✅ | — | JWT signing key (≥ 32 ký tự) |
| `ENVIRONMENT` | ❌ | `development` | `development` hoặc `production` |
| `ALLOWED_ORIGINS` | ❌ | `*` | Danh sách domain được phép (production) |
| `API_HOST` | ❌ | `0.0.0.0` | Host binding |
| `API_PORT` | ❌ | `8000` | Port binding |
| `DEBUG` | ❌ | `True` | Debug mode |

### Frontend `frontend/config.py`

| Biến | Mặc định | Mô tả |
|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | URL của FastAPI backend |
| `COOKIE_PASSWORD` | — | Key để mã hóa cookie phía frontend |

---

## 📡 API Endpoints

### Auth (`/users`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `POST` | `/users/register` | ❌ | Đăng ký tài khoản mới |
| `POST` | `/users/login` | ❌ | Đăng nhập, trả về JWT |
| `POST` | `/users/logout` | ✅ | Đăng xuất, blacklist token |
| `POST` | `/users/refresh` | ❌* | Làm mới access token |
| `GET` | `/users/profile` | ✅ | Lấy thông tin người dùng |
| `PUT` | `/users/update` | ✅ | Cập nhật hồ sơ |
| `PUT` | `/users/change-password` | ✅ | Đổi mật khẩu |

> *Cần refresh_token cookie

### Camera (`/camera`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `GET` | `/camera/list` | ❌ | Danh sách camera khả dụng |
| `GET` | `/camera/status` | ✅ | Trạng thái camera hiện tại |
| `POST` | `/camera/start` | ✅ | Bắt đầu phiên giám sát |
| `POST` | `/camera/stop` | ✅ | Dừng phiên giám sát |
| `GET` | `/camera/video_feed` | ✅ | MJPEG stream |

### Frames (`/frames`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `GET` | `/frames/{session_id}` | ✅ | Danh sách frames của phiên |
| `GET` | `/frames/detail/{frame_id}` | ✅ | Chi tiết 1 frame + detections |
| `GET` | `/frames/analysis/{session_id}` | ✅ | Phân tích tổng hợp phiên |

### History (`/history`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `GET` | `/history/sessions` | ✅ | Danh sách phiên (có phân trang, tìm kiếm) |
| `GET` | `/history/summary` | ✅ | Tổng số phiên / phiên trong tháng |
| `GET` | `/history/session/{id}` | ✅ | Chi tiết 1 phiên đầy đủ |
| `DELETE` | `/history/session/{id}` | ✅ | Xóa phiên và toàn bộ dữ liệu liên quan |

### Statistics (`/stats`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `GET` | `/stats/daily` | ✅ | Thống kê theo ngày (7 ngày gần nhất) |

### AI Result (`/ai-result`)

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `PATCH` | `/ai-result/{result_id}` | ✅ | Cập nhật nhãn nhận diện thủ công |

### System

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| `GET` | `/health` | ❌ | Health check |
| `GET` | `/docs` | ❌ | Swagger UI |

---

## 🔐 Bảo mật

### JWT Token Strategy

```
Access Token:  1 giờ   → Dùng cho mọi API request
Refresh Token: 7 ngày  → Chỉ dùng để làm mới access token
```

Cả hai token được gửi qua:
- **Cookie** (httponly=True): Tự động gửi bởi browser
- **Authorization Header** (`Bearer <token>`): Cho programmatic access

### Rate Limiting

| Endpoint | Giới hạn |
|---|---|
| `POST /users/login` | 5 lần / 15 phút / IP |
| `POST /users/register` | 5 lần / 15 phút / IP |

### Password Security

- **Bcrypt** với cost factor mặc định (~100ms/hash)
- Không lưu mật khẩu plaintext trong database
- Validation: tối thiểu 6 ký tự, 1 chữ hoa, 1 chữ số

---

## 📸 Giao diện

### Trang chủ — Giám sát thời gian thực
- Feed camera MJPEG trực tiếp
- Countdown timer 30 giây đến lần chụp tiếp theo
- Danh sách khung hình đã trích xuất

### Phân tích phiên — Grid view
- 6 thẻ frame mỗi trang (3 cột × 2 hàng)
- Status badge: ✅ ĐANG HOẠT ĐỘNG / ⚠️ CẢNH BÁO
- Counter: Tập trung / Buồn ngủ per frame

### Chi tiết khung hình — Interactive
- Ảnh gốc với bounding box overlay
- **Click vào bounding box** → đổi nhãn (Tập trung ↔ Buồn ngủ)
- Gọi `PATCH /ai-result/{id}` ngay lập tức
- Bảng danh sách tất cả học sinh trong frame

### Thống kê — Dashboard KPI
- 4 KPI cards: Tổng lớp học / Video phân tích / Ảnh trích xuất / Sinh viên phát hiện
- Bar chart xu hướng buồn ngủ theo ngày trong tuần

---

## 🧑‍💻 Hướng dẫn phát triển

### Kiểm tra backend

```bash
cd backend
python tests/test_security.py
```

### Cấu trúc service layer (Frontend)

Mọi API call **phải đi qua `services/`**, không gọi trực tiếp trong pages:

```python
# ✅ Đúng — gọi qua service
from services.history_api import get_history, delete_session
sessions = get_history(st.session_state.client, skip=0, limit=5)

# ❌ Sai — gọi trực tiếp trong page
res = st.session_state.client.get(f"{API_BASE_URL}/history/sessions")
```

### Quy tắc CSS

Mọi styling **phải ở trong file CSS tương ứng** trong `styles/`:

```python
# ✅ Đúng
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ❌ Sai — inline style
st.markdown('<hr style="margin: 16px 0; border-color: #e2e8f0;">', unsafe_allow_html=True)
```

### Thêm page mới

1. Tạo `frontend/pages/my_page.py`
2. Tạo `frontend/styles/my_page.css`
3. Tạo service functions trong `frontend/services/`
4. Thêm vào sidebar tại `frontend/components/app_sidebar.py`

### Database Schema (tóm tắt)

```
Users
 └── Sessions (user_id → FK)
      └── Frames (session_id → FK)
           └── AIResults (frame_id → FK)
                └── Statistics (session_id → FK)
```

---

## 🗂️ Files không commit lên Git

Các file/thư mục sau được bỏ qua bởi `.gitignore`:

| File/Thư mục | Lý do |
|---|---|
| `backend/.env` | Chứa credentials nhạy cảm |
| `images/` | Ảnh runtime do camera tạo ra (hàng trăm MB) |
| `venv/` | Virtual environment |
| `__pycache__/` | Python bytecode |
| `*.log` | Log files |
| `*.db`, `*.sqlite` | Database files |



---

## 📌 Lưu ý triển khai Production

- [ ] Đổi `SECRET_KEY` thành chuỗi ngẫu nhiên đủ mạnh (≥ 32 ký tự)
- [ ] Đặt `ENVIRONMENT=production` trong `.env`
- [ ] Cấu hình `ALLOWED_ORIGINS` đúng domain frontend
- [ ] Bật HTTPS/SSL
- [ ] Cân nhắc dùng **Redis** cho token blacklist (thay thế in-memory)
- [ ] Cấu hình reverse proxy (Nginx/Caddy) phía trước Uvicorn
- [ ] Đặt `images/` lên object storage (S3, MinIO) thay vì local disk

---

## 📄 License

MIT License — xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<div align="center">

**EduVision AI** — Đồ án Tốt nghiệp · 2026  
Xây dựng bằng ❤️ với FastAPI, Streamlit & YOLOv8

</div>

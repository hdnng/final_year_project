import time
import requests
import streamlit as st

from streamlit_autorefresh import st_autorefresh
from components.app_sidebar import render_sidebar
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.load_css import load_css
from utils.auth_guard import require_auth

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(
    layout="wide",
    page_title="Giám sát"
)

API_URL = "http://127.0.0.1:8000/camera"

# ======================================================
# STYLE
# ======================================================
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/home.css"), unsafe_allow_html=True)

# ======================================================
# SESSION STATE
# ======================================================
DEFAULTS = {
    "is_login": False,
    "access_token_value": None,
    "refresh_token_value": None,
    "running": False,
    "session_id": None,
    "frame_id": None,
    "capture_start_time": None,
    "refresh_key": 0,
    "page_loaded": ""
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "client" not in st.session_state:
    st.session_state.client = requests.Session()

client = st.session_state.client

# ======================================================
# AUTH
# ======================================================
require_auth()

# ======================================================
# HELPERS
# ======================================================
def get_auth_headers():
    token = (
        st.session_state.get("token")
        or st.session_state.get("access_token_value")
    )

    if token:
        return {
            "Authorization": f"Bearer {token}"
        }

    return {}


def safe_get(url, timeout=5):
    try:
        return client.get(
            url,
            headers=get_auth_headers(),
            timeout=timeout
        )
    except:
        return None


def safe_post(url, params=None, timeout=10):
    try:
        return client.post(
            url,
            params=params,
            headers=get_auth_headers(),
            timeout=timeout
        )
    except:
        return None


# ======================================================
# PAGE ENTER
# ======================================================
if st.session_state["page_loaded"] != "home":
    st.session_state["page_loaded"] = "home"
    st.session_state["refresh_key"] += 1

# ======================================================
# BACKEND STATUS SYNC
# ======================================================
status_res = safe_get(f"{API_URL}/status")

if status_res and status_res.status_code == 200:
    try:
        data = status_res.json()

        backend_running = data.get("running", False)
        backend_session = data.get("session_id")

        old_running = st.session_state["running"]

        st.session_state["running"] = backend_running
        st.session_state["session_id"] = backend_session

        # vừa quay lại page hoặc backend đang chạy
        if backend_running and not old_running:
            st.session_state["capture_start_time"] = time.time()

        if backend_running and not st.session_state["capture_start_time"]:
            st.session_state["capture_start_time"] = time.time()

        if not backend_running:
            st.session_state["capture_start_time"] = None

    except:
        pass

# ======================================================
# SIDEBAR
# ======================================================
hide_sidebar()
render_sidebar(active="home")

# ======================================================
# HEADER
# ======================================================
st.markdown(
    '<div class="page-title">Giám sát thời gian thực</div>',
    unsafe_allow_html=True
)

# ======================================================
# CAMERA LIST
# ======================================================
cams = []

cams_res = safe_get(f"{API_URL}/list")

if cams_res:
    if cams_res.status_code == 200:
        cams = cams_res.json().get("cameras", [])

    elif cams_res.status_code == 401:
        st.error("Phiên đăng nhập hết hạn")

        if st.button("Đăng nhập lại"):
            st.session_state.clear()
            st.switch_page("pages/login.py")

        st.stop()

# ======================================================
# TOP CONTROL
# ======================================================
col1, col2, col3 = st.columns([2, 1, 1])

# -------------------------
# LEFT INPUT
# -------------------------
with col1:
    class_id = st.text_input(
        "Nhập mã lớp",
        placeholder="VD: 10A1"
    )

    if cams:
        selected_cam = st.selectbox(
            "Chọn camera",
            cams,
            format_func=lambda x: x.get("name", "Unknown")
        )
        camera_index = selected_cam["index"]
    else:
        st.warning("Không có camera")
        camera_index = None

# -------------------------
# START
# -------------------------
with col2:
    st.write("")
    st.write("")

    if not st.session_state["running"]:

        disabled = (
            not class_id.strip()
            or camera_index is None
        )

        if st.button(
            "🟢 Bắt đầu phân tích",
            use_container_width=True,
            disabled=disabled
        ):
            res = safe_post(
                f"{API_URL}/start",
                params={
                    "camera_index": camera_index,
                    "class_id": class_id.strip()
                }
            )

            if res and res.status_code == 200:
                data = res.json()

                st.session_state["running"] = True
                st.session_state["session_id"] = data.get("session_id")
                st.session_state["capture_start_time"] = time.time()
                st.session_state["refresh_key"] += 1

                st.rerun()

            else:
                st.error("Không thể bắt đầu camera")

# -------------------------
# STOP
# -------------------------
with col3:
    st.write("")
    st.write("")

    if st.session_state["running"]:
        if st.button(
            "🔴 Dừng phân tích",
            use_container_width=True
        ):
            safe_post(
                f"{API_URL}/stop",
                timeout=5
            )

            st.session_state["running"] = False
            st.session_state["session_id"] = None
            st.session_state["capture_start_time"] = None
            st.session_state["refresh_key"] += 1

            st.rerun()

# ======================================================
# MAIN LAYOUT
# ======================================================
left_col, right_col = st.columns([3.3, 1.2])

# ======================================================
# LEFT PANEL
# ======================================================
with left_col:

    st.markdown(
        '<div class="card-box">',
        unsafe_allow_html=True
    )

    st.subheader("Camera realtime")

    if st.session_state["running"]:

        cam_w = 1280
        cam_h = 720

        info_res = safe_get(f"{API_URL}/info")

        if info_res and info_res.status_code == 200:
            try:
                info = info_res.json()
                cam_w = info.get("width", 1280)
                cam_h = info.get("height", 720)
            except:
                pass

        if cam_w <= 0 or cam_h <= 0:
            cam_w, cam_h = 1280, 720

        st.markdown(f"""
        <div style="
            width:100%;
            aspect-ratio:{cam_w}/{cam_h};
            background:black;
            border-radius:14px;
            overflow:hidden;
            display:flex;
            align-items:center;
            justify-content:center;
        ">
            <img
                src="{API_URL}/video_feed"
                style="
                    width:100%;
                    height:100%;
                    object-fit:contain;
                ">
        </div>
        """, unsafe_allow_html=True)

        # progress
        start_time = st.session_state["capture_start_time"]

        if start_time:
            elapsed = time.time() - start_time
            cycle = elapsed % 30

            percent = int((cycle / 30) * 100)
            remain = max(0, int(30 - cycle))

            st.progress(
                percent,
                text=f"Đang trích xuất khung hình... {remain}s"
            )

    else:
        st.info("Nhấn Bắt đầu để mở camera")

    st.markdown("</div>", unsafe_allow_html=True)

# ======================================================
# RIGHT PANEL
# ======================================================
with right_col:

    st.markdown(
        '<div class="right-card">',
        unsafe_allow_html=True
    )

    st.subheader("Khung hình trích xuất")

    if (
        st.session_state["running"]
        and st.session_state["session_id"]
    ):
        frame_res = safe_get(
            f"{API_URL}/frames/{st.session_state['session_id']}"
        )

        if frame_res and frame_res.status_code == 200:

            try:
                frames = frame_res.json()
            except:
                frames = []

            if not frames:
                st.info("Chưa có ảnh")

            else:
                box = st.container(
                    height=720,
                    border=False
                )

                with box:
                    for frame in frames:

                        img_path = frame.get("image_path")

                        if not img_path:
                            continue

                        st.markdown(
                            '<div class="frame-item">',
                            unsafe_allow_html=True
                        )

                        st.image(
                            img_path,
                            use_container_width=True
                        )

                        st.caption(
                            f"Frame #{frame['frame_id']}"
                        )

                        st.caption(
                            frame.get(
                                "extracted_at",
                                ""
                            )
                        )

                        if st.button(
                            "Xem chi tiết",
                            key=f"detail_{frame['frame_id']}",
                            use_container_width=True
                        ):
                            st.session_state["frame_id"] = frame["frame_id"]
                            st.switch_page(
                                "pages/frame_detail.py"
                            )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True
                        )

        else:
            st.warning("Không load được frame")

    else:
        st.info("Chưa bắt đầu session")

    if st.session_state["running"]:
        if st.button(
            "XEM TẤT CẢ",
            use_container_width=True
        ):
            st.switch_page(
                "pages/session_analysis.py"
            )

    st.markdown("</div>", unsafe_allow_html=True)

# ======================================================
# AUTO REFRESH
# ======================================================
if st.session_state["running"]:
    st_autorefresh(
        interval=1000,
        key=f"refresh_{st.session_state['refresh_key']}"
    )
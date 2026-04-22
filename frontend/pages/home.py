"""Home page — real-time camera monitoring dashboard."""

import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from components.app_sidebar import render_sidebar
from config import API_BASE_URL
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state, safe_get, safe_post
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Giám sát")

CAMERA_URL = f"{API_BASE_URL}/camera"

# ── Styles ──────────────────────────────────────────────────
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/home.css"), unsafe_allow_html=True)

# ── Session State ───────────────────────────────────────────
init_session_state()

# ── Auth ────────────────────────────────────────────────────
require_auth()

# ── Page Enter ──────────────────────────────────────────────
if st.session_state["page_loaded"] != "home":
    st.session_state["page_loaded"] = "home"
    st.session_state["refresh_key"] += 1

# ── Sync with Backend ──────────────────────────────────────
status_res = safe_get(f"{CAMERA_URL}/status")

if status_res and status_res.status_code == 200:
    try:
        data = status_res.json()
        backend_running = data.get("running", False)
        backend_session = data.get("session_id")
        old_running = st.session_state["running"]

        st.session_state["running"] = backend_running
        st.session_state["session_id"] = backend_session

        if backend_running and not old_running:
            st.session_state["capture_start_time"] = time.time()
        if backend_running and not st.session_state["capture_start_time"]:
            st.session_state["capture_start_time"] = time.time()
        if not backend_running:
            st.session_state["capture_start_time"] = None
    except Exception:
        pass

# ── Sidebar ─────────────────────────────────────────────────
hide_sidebar()
render_sidebar(active="home")

# ── Header ──────────────────────────────────────────────────
st.markdown(
    '<div class="page-title">Giám sát thời gian thực</div>',
    unsafe_allow_html=True,
)

# ── Camera List ─────────────────────────────────────────────
cams = []
cams_res = safe_get(f"{CAMERA_URL}/list")

if cams_res:
    if cams_res.status_code == 200:
        cams = cams_res.json().get("cameras", [])
    elif cams_res.status_code == 401:
        st.error("Phiên đăng nhập hết hạn")
        if st.button("Đăng nhập lại"):
            st.session_state.clear()
            st.switch_page("pages/login.py")
        st.stop()

# ── Controls ────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    class_id = st.text_input("Nhập mã lớp", placeholder="VD: 10A1")

    if cams:
        selected_cam = st.selectbox(
            "Chọn camera", cams,
            format_func=lambda x: x.get("name", "Unknown"),
        )
        camera_index = selected_cam["index"]
    else:
        st.warning("Không có camera")
        camera_index = None

with col2:
    st.write("")
    st.write("")
    if not st.session_state["running"]:
        disabled = not class_id.strip() or camera_index is None
        if st.button("🟢 Bắt đầu phân tích", use_container_width=True, disabled=disabled):
            res = safe_post(
                f"{CAMERA_URL}/start",
                params={"camera_index": camera_index, "class_id": class_id.strip()},
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

with col3:
    st.write("")
    st.write("")
    if st.session_state["running"]:
        if st.button("🔴 Dừng phân tích", use_container_width=True):
            safe_post(f"{CAMERA_URL}/stop", timeout=5)
            st.session_state["running"] = False
            st.session_state["session_id"] = None
            st.session_state["capture_start_time"] = None
            st.session_state["refresh_key"] += 1
            st.rerun()

# ── Main Layout ─────────────────────────────────────────────
left_col, right_col = st.columns([3.3, 1.2])

# Left panel — camera feed
with left_col:
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.subheader("Camera realtime")

    if st.session_state["running"]:
        cam_w, cam_h = 1280, 720
        info_res = safe_get(f"{CAMERA_URL}/info")
        if info_res and info_res.status_code == 200:
            try:
                info = info_res.json()
                cam_w = info.get("width", 1280)
                cam_h = info.get("height", 720)
            except Exception:
                pass
        if cam_w <= 0 or cam_h <= 0:
            cam_w, cam_h = 1280, 720

        st.markdown(f"""
        <div style="
            width:100%; aspect-ratio:{cam_w}/{cam_h};
            background:black; border-radius:14px;
            overflow:hidden; display:flex;
            align-items:center; justify-content:center;
        ">
            <img src="{CAMERA_URL}/video_feed"
                 style="width:100%; height:100%; object-fit:contain;">
        </div>
        """, unsafe_allow_html=True)

        # Capture progress bar
        start_time = st.session_state["capture_start_time"]
        if start_time:
            elapsed = time.time() - start_time
            cycle = elapsed % 30
            percent = int((cycle / 30) * 100)
            remain = max(0, int(30 - cycle))
            st.progress(percent, text=f"Đang trích xuất khung hình... {remain}s")
    else:
        st.info("Nhấn Bắt đầu để mở camera")

    st.markdown("</div>", unsafe_allow_html=True)

# Right panel — extracted frames
with right_col:
    st.markdown('<div class="right-card">', unsafe_allow_html=True)
    st.subheader("Khung hình trích xuất")

    if st.session_state["running"] and st.session_state["session_id"]:
        sid = st.session_state["session_id"]
        frame_res = safe_get(f"{API_BASE_URL}/frames/{sid}")

        if frame_res and frame_res.status_code == 200:
            try:
                frames = frame_res.json()
            except Exception:
                frames = []

            if not frames:
                st.info("Chưa có ảnh")
            else:
                box = st.container(height=720, border=False)
                with box:
                    for frame in frames:
                        img_path = frame.get("image_path")
                        if not img_path:
                            continue

                        st.markdown('<div class="frame-item">', unsafe_allow_html=True)
                        st.image(img_path, use_container_width=True)
                        st.caption(f"Frame #{frame['frame_id']}")
                        st.caption(frame.get("extracted_at", ""))

                        if st.button(
                            "Xem chi tiết",
                            key=f"detail_{frame['frame_id']}",
                            use_container_width=True,
                        ):
                            st.session_state["frame_id"] = frame["frame_id"]
                            st.switch_page("pages/frame_detail.py")

                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Không load được frame")
    else:
        st.info("Chưa bắt đầu session")

    if st.session_state["running"]:
        if st.button("XEM TẤT CẢ", use_container_width=True):
            st.switch_page("pages/session_analysis.py")

    st.markdown("</div>", unsafe_allow_html=True)

# ── Auto Refresh ────────────────────────────────────────────
if st.session_state["running"]:
    st_autorefresh(
        interval=1000,
        key=f"refresh_{st.session_state['refresh_key']}",
    )
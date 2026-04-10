import streamlit as st
import requests
from PIL import Image
from pathlib import Path

from streamlit_autorefresh import st_autorefresh
from components.app_sidebar import render_sidebar
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.load_css import load_css
from utils.auth_guard import require_auth

st.set_page_config(layout="wide")
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

# ===== INIT SESSION STATE (CRITICAL!) =====
if "is_login" not in st.session_state:
    st.session_state["is_login"] = False
if "access_token_value" not in st.session_state:
    st.session_state["access_token_value"] = None
if "refresh_token_value" not in st.session_state:
    st.session_state["refresh_token_value"] = None
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ===== AUTH CHECK =====
require_auth()

if "running" not in st.session_state:
    st.session_state["running"] = False

API_URL = "http://127.0.0.1:8000/camera"  # ✅ Fixed: /camera not /cameras

# ===== SIDEBAR =====
hide_sidebar()
render_sidebar(active="home")

# ===== HEADER =====
st.markdown("##  Giám sát thời gian thực")

# ===== HELPERS =====
def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

# ===== CONTROL =====
col_top1, col_top2, col_top3 = st.columns([2, 1, 1])

# ❉ nhập mã lớp
with col_top1:
    class_id = st.text_input("Nhập mã lớp", placeholder="VD: 10A1")

    if not class_id.strip():
        st.info("Vui lòng nhập mã lớp để bắt đầu")

# ===== lấy camera =====
try:
    client = st.session_state.client
    headers = get_auth_headers()
    cams_res = client.get(f"{API_URL}/list", headers=headers)

    if cams_res.status_code == 200:
        cams = cams_res.json().get("cameras", [])
    elif cams_res.status_code == 401:
        st.error("❌ Phiên đăng nhập hết hạn")
        if st.button("🔄 Đăng nhập lại"):
            st.session_state.clear()
            st.switch_page("pages/login.py")
        st.stop()
    else:
        st.error(f"❌ Lỗi lấy camera: {cams_res.status_code}")
        cams = []

except Exception as e:
    st.error(f"❌ Lỗi kết nối: {str(e)}")
    cams = []

if len(cams) > 0:
    selected_cam = st.selectbox(
        "Chọn camera",
        cams,
        format_func=lambda x: x.get("name", "Unknown")
    )

    camera_index = selected_cam.get("index")
else:
    st.warning("❌ Không có camera nào")
    camera_index = None


# ===== BUTTON CONTROL =====
with col_top2:
    if not st.session_state["running"]:
        start_disabled = (not class_id.strip()) or (camera_index is None)

        if st.button("🟢 Bắt đầu phân tích", disabled=start_disabled):
            try:
                with st.spinner("Đang bắt đầu..."):
                    headers = get_auth_headers()
                    res = st.session_state.client.post(
                        f"{API_URL}/start",
                        params={
                            "camera_index": camera_index,
                            "class_id": class_id.strip()
                        },
                        headers=headers
                    )

                if res.status_code == 200:
                    data = res.json()
                    st.success(data.get("message", "✅ Đã bắt đầu phân tích"))
                    st.session_state["running"] = True
                    st.session_state["session_id"] = data.get("session_id")
                    st.rerun()

                elif res.status_code == 401:
                    st.error("❌ Phiên đăng nhập hết hạn")
                else:
                    try:
                        error_msg = res.json().get("detail", res.text)
                    except Exception:
                        error_msg = res.text
                    st.error(f"❌ Lỗi: {error_msg}")

            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {str(e)}")

with col_top3:
    if st.session_state["running"]:
        if st.button("🔴 Dừng phân tích"):
            try:
                with st.spinner("Đang dừng..."):
                    headers = get_auth_headers()
                    res = st.session_state.client.post(f"{API_URL}/stop", headers=headers)

                if res.status_code == 200:
                    st.warning(res.json().get("message", "⏹️ Đã dừng phân tích"))
                    st.session_state["running"] = False
                    st.rerun()

                elif res.status_code == 401:
                    st.error("❌ Phiên đăng nhập hết hạn")
                else:
                    try:
                        error_msg = res.json().get("detail", res.text)
                    except Exception:
                        error_msg = res.text
                    st.error(f"❌ Lỗi: {error_msg}")

            except Exception as e:
                st.error(f"❌ Lỗi kết nối: {str(e)}")

# ===== MAIN LAYOUT =====
left_col, right_col = st.columns([3, 1])

# ===== LEFT: CAMERA STATUS =====
with left_col:
    st.markdown("###  Camera realtime")

    if st.session_state.get("running", False):
        try:
            # ✅ Use iframe để display MJPEG stream (st.image không hỗ trợ streaming)
            st.markdown(f"""
            <img src="http://127.0.0.1:8000/camera/video_feed"
                 style="width:100%; border-radius: 8px; height: auto;">
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Không thể load video: {str(e)}")
    else:
        st.info("Nhấn Bắt đầu để mở camera")

# ===== RIGHT: IMAGE PANEL =====
with right_col:
    st.markdown("### Khung hình trích xuất")

    if st.session_state.get("running") and st.session_state.get("session_id"):
        try:
            headers = get_auth_headers()
            res = st.session_state.client.get(
                f"{API_URL}/frames/{st.session_state['session_id']}",
                headers=headers
            )

            if res.status_code == 200:
                frames = res.json()

                if len(frames) == 0:
                    st.info("Chưa có ảnh")
                else:
                    for frame in frames[:6]:
                        img_path = frame.get("image_path")
                        if img_path:
                            try:
                                st.image(img_path, use_container_width=True)
                                st.caption(frame.get("extracted_at", ""))
                            except Exception as e:
                                st.warning(f"⚠️ Lỗi load ảnh: {str(e)}")

            elif res.status_code == 401:
                st.error("❌ Phiên đăng nhập hết hạn")
            else:
                st.warning(f"⚠️ Lỗi: {res.status_code}")

        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {str(e)}")
    else:
        st.info("Chưa bắt đầu session")

# ===== AUTO REFRESH =====
if st.session_state.get("running", False):
    st_autorefresh(interval=30000, key="refresh")
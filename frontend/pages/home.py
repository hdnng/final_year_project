import streamlit as st
import requests
import os
from PIL import Image
from pathlib import Path

from  streamlit_autorefresh import st_autorefresh
from components.app_sidebar import render_sidebar
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.load_css import load_css
st.set_page_config(layout="wide")
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

if "running" not in st.session_state:
    st.session_state["running"] = False

API_URL = "http://127.0.0.1:8000/camera"

# ===== SIDEBAR =====

hide_sidebar()
render_sidebar(active="home")

# ===== HEADER =====

st.markdown("##  Giám sát thời gian thực")

# ===== CONTROL =====

col_top1, col_top2, col_top3 = st.columns([2,1,1])
 
# 🔥 nhập mã lớp
with col_top1:
    class_id = st.text_input("Nhập mã lớp", placeholder="VD: 10A1")

    if not class_id.strip():
        st.info("Vui lòng nhập mã lớp để bắt đầu")

# ===== lấy camera =====
try:
    cams = requests.get(f"{API_URL}/list").json()["cameras"]
except Exception as e:
    st.error(f"Không lấy được camera: {e}")
    cams = []

if len(cams) > 0:
    selected_cam = st.selectbox(
        "Chọn camera",
        cams,
        format_func=lambda x: x["name"]   # 🔥 hiển thị tên thật
    )

    camera_index = selected_cam["index"]  # 🔥 lấy index đúng
else:
    st.warning("Không có camera nào")
    camera_index = None


# ===== BUTTON CONTROL =====
with col_top2:
    if not st.session_state["running"]:
        start_disabled = (not class_id.strip()) or (camera_index is None)

        if st.button("🟢 Bắt đầu phân tích", disabled=start_disabled):
            try:
                res = requests.post(
                    f"{API_URL}/start",
                    params={
                        "camera_index": camera_index,
                        "class_id": class_id.strip()
                    }
                )

                data = res.json()

                st.success(data.get("message", "Đã bắt đầu"))

                st.session_state["running"] = True
                st.session_state["session_id"] = data.get("session_id")

                st.rerun()  # 🔥 cập nhật UI ngay

            except Exception as e:
                st.error(f"Lỗi khi gọi API: {e}")

with col_top3:
    if st.session_state["running"]:
        if st.button("🔴 Dừng phân tích"):
            try:
                res = requests.post(f"{API_URL}/stop")

                st.warning(res.json().get("message", "Đã dừng"))

                st.session_state["running"] = False

                st.rerun()  # 🔥 cập nhật UI

            except Exception as e:
                st.error(f"Lỗi khi stop: {e}")
# ===== MAIN LAYOUT =====
left_col, right_col = st.columns([3,1])

# ===== LEFT: CAMERA STATUS =====
with left_col:
    st.markdown("###  Camera realtime")

    if st.session_state.get("running", False):
        st.image("http://127.0.0.1:8000/camera/video_feed")
    else:
        st.info("Nhấn Bắt đầu để mở camera")

# ===== RIGHT: IMAGE PANEL =====
with right_col:
    st.markdown("### Khung hình trích xuất")

    if st.session_state.get("running") and st.session_state.get("session_id"):
        try:
            res = requests.get(
                f"{API_URL}/frames/{st.session_state['session_id']}"
            )

            frames = res.json()

            if len(frames) == 0:
                st.info("Chưa có ảnh")
            else:
                for frame in frames[:6]:
                    img_path = frame["image_path"]

                    st.image(img_path, use_container_width=True)
                    st.caption(frame["extracted_at"])

        except Exception as e:
            st.error(f"Lỗi load ảnh: {e}")
    else:
        st.info("Chưa bắt đầu session")

# ===== AUTO REFRESH =====
if st.session_state.get("running", False):
    st_autorefresh(interval=30000, key="refresh") #30s
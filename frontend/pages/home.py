import streamlit as st
import requests
import os
from PIL import Image
from pathlib import Path

st.set_page_config(layout="wide")

API_URL = "http://127.0.0.1:8000/camera"

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## 🎓 EduVision AI")
    st.markdown("Phân tích hành vi người học")

    st.markdown("---")
    st.button("📹 Giám sát")
    st.button("📊 Thống kê")
    st.button("📁 Lịch sử")
    st.button("⚙️ Cài đặt")

# ===== HEADER =====
st.markdown("## 📹 Giám sát thời gian thực")

# ===== CONTROL =====
col_top1, col_top2, col_top3 = st.columns([2,1,1])

with col_top1:
    st.selectbox("Chọn lớp học", ["Lớp 10A1 - Phòng 201"])

with col_top2:
    if st.button("🟢 Bắt đầu phân tích"):
        try:
            res = requests.post(f"{API_URL}/start")
            st.success(res.json()["message"])
            st.session_state["running"] = True
        except:
            st.error("Không gọi được API")

with col_top3:
    if st.button("🔴 Dừng phân tích"):
        try:
            res = requests.post(f"{API_URL}/stop")
            st.warning(res.json()["message"])
            st.session_state["running"] = False
        except:
            st.error("Không gọi được API")

# ===== MAIN LAYOUT =====
left_col, right_col = st.columns([3,1])

# ===== LEFT: CAMERA STATUS =====
with left_col:
    st.markdown("### 🎥 Camera realtime")

    if st.session_state.get("running", False):
        st.image("http://127.0.0.1:8000/camera/video_feed")
    else:
        st.info("Nhấn Bắt đầu để mở camera")

# ===== RIGHT: IMAGE PANEL =====
with right_col:
    st.markdown("### 📸 Ảnh chụp mỗi 30s")

    BASE_DIR = Path(__file__).resolve().parents[2]  # về project_root
    image_folder = BASE_DIR / "images"

    if os.path.exists(image_folder):
        images = sorted(os.listdir(image_folder), reverse=True)

        if len(images) == 0:
            st.info("Chưa có ảnh")
        else:
            for img_name in images[:6]:
                img_path = os.path.join(image_folder, img_name)

                try:
                    img = Image.open(img_path)
                    st.image(img, use_container_width=True)
                    st.caption(img_name)
                except:
                    pass

# ===== AUTO REFRESH =====
if st.session_state.get("running", False):
    st.rerun()
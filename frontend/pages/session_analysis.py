# pages/session_analysis.py

import streamlit as st
import requests
import math

from components.app_sidebar import render_sidebar
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.load_css import load_css
from utils.auth_guard import require_auth

# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Kết quả phân tích")

# ================= INIT =================
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

if "analysis_page" not in st.session_state:
    st.session_state.analysis_page = 1

# ================= AUTH =================
require_auth()

# ================= UI =================
hide_sidebar()
render_sidebar(active="home")
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

# ================= CSS =================
st.markdown(load_css("styles/session_analysis.css"), unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/camera"

# ================= TOKEN =================
def get_auth_headers():
    token = st.session_state.get("token")

    if not token:
        token = st.session_state.get("access_token_value")

    if token:
        return {"Authorization": f"Bearer {token}"}

    return {}

# ================= SESSION =================
session_id = st.session_state.get("session_id")

if not session_id:
    st.warning("Không có phiên học đang chạy.")
    st.stop()

# ================= GET SESSION INFO =================
class_name = "UNKNOWN"

try:
    res = st.session_state.client.get(
        f"{API_URL}/sessions",
        headers=get_auth_headers()
    )

    if res.status_code == 200:
        sessions = res.json()

        for s in sessions:
            if s["session_id"] == session_id:
                class_name = s["class_id"]
                break
except:
    pass

# ================= GET ANALYSIS DATA =================
frames = []

try:
    res = st.session_state.client.get(
        f"{API_URL}/analysis/{session_id}",
        headers=get_auth_headers()
    )

    if res.status_code == 200:
        frames = res.json()

except:
    pass

# ================= HEADER =================
if st.button("← Danh sách khung hình"):
    st.switch_page("pages/home.py")

st.markdown(
    '<div class="main-title">Kết quả Phân tích Phiên học</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'''
    <span class="badge">{class_name}</span>
    <span class="subtext">Phiên học đang chạy</span>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-title">Dòng thời gian trích xuất (Mỗi 30 giây)</div>',
    unsafe_allow_html=True
)

# ================= EMPTY =================
if len(frames) == 0:
    st.info("Chưa có dữ liệu phân tích.")
    st.stop()

# ================= PAGINATION =================
per_page = 6
total = len(frames)
pages = max(1, math.ceil(total / per_page))

page = st.session_state.analysis_page

if page > pages:
    page = pages
    st.session_state.analysis_page = page

start = (page - 1) * per_page
end = start + per_page

show_frames = frames[start:end]

# ================= GRID =================
cols = st.columns(3)

for i, item in enumerate(show_frames):

    with cols[i % 3]:

        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.image(item["image_path"], use_container_width=True)

        # ===== ĐỔI #1 #2 THÀNH ID FRAME THẬT =====
        st.markdown(
            f'<div class="card-title">Phân tích khung hình #{item["frame_id"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="card-time">Trích xuất lúc {item["extracted_at"]}</div>',
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="label">TẬP TRUNG</div>
                <div class="blue">{item["focus_count"]:02d}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            red_class = "stat-box stat-red" if item["sleeping_count"] > 0 else "stat-box"

            st.markdown(f"""
            <div class="{red_class}">
                <div class="label">BUỒN NGỦ</div>
                <div class="red">{item["sleeping_count"]:02d}</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button(
            "Xem chi tiết",
            use_container_width=True,
            key=f"detail_{item['frame_id']}"
        ):
            st.session_state["frame_id"] = item["frame_id"]
            st.switch_page("pages/frame_detail.py")

        st.markdown('</div>', unsafe_allow_html=True)
# ================= FOOTER =================
st.markdown(
    f'<div class="footer">Hiển thị {len(show_frames)} trong số {total} khung hình</div>',
    unsafe_allow_html=True
)

p1,p2,p3,p4,p5 = st.columns([5,1,1,1,5])

with p2:
    if st.button("‹", use_container_width=True, disabled=(page <= 1)):
        st.session_state.analysis_page -= 1
        st.rerun()

with p3:
    st.button(str(page), use_container_width=True, disabled=True)

with p4:
    if st.button("›", use_container_width=True, disabled=(page >= pages)):
        st.session_state.analysis_page += 1
        st.rerun()



from streamlit_autorefresh import st_autorefresh

if st.session_state.get("running", False):
    st_autorefresh(interval=10000, key="analysis_refresh")
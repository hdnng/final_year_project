import streamlit as st
import pandas as pd
import requests
import plotly.express as px

from utils.auth_guard import require_auth
from utils.load_css import load_css
from utils.hide_streamlit_sidebar import hide_sidebar

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

API_URL = "http://127.0.0.1:8000"

# ================= sidebar =================
hide_sidebar()
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar()

# ===== GET PARAM =====
session_id = st.session_state.get("selected_session")

if not session_id:
    st.error("❌ Thiếu session_id")
    st.stop()

try:
    session_id = int(session_id)
except ValueError:
    st.error("❌ ID phiên không hợp lệ")
    st.stop()

# ===== API =====
def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_detail(session, session_id):
    """Lấy chi tiết phiên"""
    try:
        headers = get_auth_headers()
        res = session.get(f"{API_URL}/history/session/{session_id}", headers=headers)

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.error("❌ Phiên đăng nhập hết hạn")
            return None
        elif res.status_code == 404:
            st.error("❌ Không tìm thấy phiên này")
            return None
        else:
            st.error(f"❌ Lỗi: {res.status_code}")
            return None

    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {str(e)}")
        return None

# ===== GET CLIENT AND DATA =====
if "client" not in st.session_state:
    st.error("❌ Lỗi: Không có session client")
    st.stop()

data = get_detail(st.session_state.client, session_id)

if not data:
    st.stop()

# ===== HEADER =====
st.title(f"📊 Chi tiết phiên #{session_id} - {data.get('class_id', 'Unknown')}")

# ===== KPI =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Tổng người", data.get("total_students", 0))
focus_rate = data.get("focus_rate", 0)
col2.metric("Độ tập trung", f"{focus_rate*100:.1f}%" if isinstance(focus_rate, (int, float)) else "N/A")
col3.metric("Cảnh báo", data.get("alerts", 0))
col4.metric("Thời gian (phút)", data.get("duration", 0))

# ===== PIE CHART =====
total_students = data.get("total_students", 0)
sleeping = data.get("sleeping", 0)

pie_data = pd.DataFrame({
    "Trạng thái": ["Bình thường", "Ngủ gật"],
    "Số lượng": [
        total_students - sleeping,
        sleeping
    ]
})

fig = px.pie(
    pie_data,
    names="Trạng thái",
    values="Số lượng",
    hole=0.4
)

st.plotly_chart(fig, use_container_width=True)

# ===== TABLE =====
frames = data.get("frames", [])

if not frames:
    st.info("📷 Chưa có khung hình trong phiên này")
    st.stop()

df = pd.DataFrame(frames)

# ===== PAGINATION =====
page_size = 5
total_rows = len(df)
total_pages = max((total_rows - 1) // page_size + 1, 1)

if "detail_page" not in st.session_state:
    st.session_state.detail_page = 1

start = (st.session_state.detail_page - 1) * page_size
end = start + page_size

df_page = df.iloc[start:end]

st.markdown("### Các khung hình phát hiện")
st.dataframe(df_page, use_container_width=True)

# ===== PAGINATION UI =====
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅️ Trang trước") and st.session_state.detail_page > 1:
        st.session_state.detail_page -= 1
        st.rerun()

with col2:
    st.markdown(
        f"<div style='text-align:center'>Trang {st.session_state.detail_page}/{total_pages}</div>",
        unsafe_allow_html=True
    )

with col3:
    if st.button("Trang sau ➡️") and st.session_state.detail_page < total_pages:
        st.session_state.detail_page += 1
        st.rerun()
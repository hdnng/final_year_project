import streamlit as st
import pandas as pd
import requests
import plotly.express as px

API_URL = "http://localhost:8000"


# ================= sidebar =================
from utils.hide_streamlit_sidebar import hide_sidebar
hide_sidebar()

from utils.load_css import load_css
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar()
# ===== GET PARAM =====
#session_id = st.query_params.get("session_id")
session_id = st.session_state.get("selected_session")

if not session_id:
    st.error("Thiếu session_id")
    st.stop()

session_id = int(session_id)

# ===== API =====
def get_detail(session_id):
    try:
        return requests.get(f"{API_URL}/history/session/{session_id}").json()
    except:
        return None

data = get_detail(session_id)

if not data:
    st.error("Không có dữ liệu")
    st.stop()

# ===== HEADER =====
st.title(f"📊 Chi tiết phiên #{session_id} - {data['class_id']}")

# ===== KPI =====
col1, col2, col3, col4 = st.columns(4)

col1.metric("Tổng người", data["total_students"])
col2.metric("Độ tập trung", f"{data['focus_rate']*100:.1f}%")
col3.metric("Cảnh báo", data["alerts"])
col4.metric("Thời gian (phút)", data["duration"])

# ===== PIE CHART =====
pie_data = pd.DataFrame({
    "Trạng thái": ["Bình thường", "Ngủ gật"],
    "Số lượng": [
        data["total_students"] - data["sleeping"],
        data["sleeping"]
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
df = pd.DataFrame(data["frames"])

# ===== PAGINATION =====
page_size = 5
total_rows = len(df)
total_pages = max((total_rows - 1)//page_size + 1, 1)

if "page" not in st.session_state:
    st.session_state.page = 1

start = (st.session_state.page - 1) * page_size
end = start + page_size

df_page = df.iloc[start:end]

st.dataframe(df_page, use_container_width=True)

# ===== PAGINATION UI =====
col1, col2, col3 = st.columns([1,2,1])

with col1:
    if st.button("⬅️") and st.session_state.page > 1:
        st.session_state.page -= 1

with col2:
    st.write(f"Trang {st.session_state.page}/{total_pages}")

with col3:
    if st.button("➡️") and st.session_state.page < total_pages:
        st.session_state.page += 1
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.express as px
from utils.load_css import load_css
from utils.auth_guard import require_auth

st.set_page_config(layout="wide", page_title="Thống kê")

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

# ================= API =================
def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_daily(session):
    """Lấy dữ liệu thống kê hàng ngày"""
    try:
        headers = get_auth_headers()
        res = session.get(f"{API_URL}/stats/daily", headers=headers)  # ✅ Fixed: /stats not /statistics

        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.error("❌ Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại")
            st.stop()
        else:
            st.error(f"❌ Lỗi: {res.status_code}")
            return []

    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {str(e)}")
        return []

# ================= CSS =================
st.markdown(load_css("styles/statistics.css"), unsafe_allow_html=True)

# ================= SIDEBAR =================
from utils.hide_streamlit_sidebar import hide_sidebar
hide_sidebar()

st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar(active="statistics")

# ================= LOAD DATA =================
client = st.session_state.client
daily_data = get_daily(client)

if not daily_data:
    st.info("📊 Chưa có dữ liệu thống kê")
    st.stop()

df = pd.DataFrame(daily_data)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ================= FILTER =================
seven_days_ago = datetime.now() - timedelta(days=7)
df_7d = df[df["date"] >= seven_days_ago]

if len(df_7d) == 0:
    st.info("📊 Chưa có dữ liệu trong 7 ngày gần đây")
    st.stop()

latest = df_7d.iloc[-1]

total = int(latest["total"])
sleeping = int(latest["sleeping"])
focus_rate = latest.get("focus_rate", 0)
normal = total - sleeping

# ================= HEADER =================
st.markdown('<div class="title">📊 Thống kê hệ thống</div>', unsafe_allow_html=True)

# ================= CARD =================
col1, col2, col3, col4 = st.columns(4, gap="large")

def render_card(col, title, value, percent, color):
    col.markdown(f"""
    <div class="card">
        <div class="sub">{title}</div>
        <div class="metric">{value}</div>
        <div class="progress">
            <div class="bar {color}" style="width:{percent}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

sleep_percent = (sleeping / total * 100) if total > 0 else 0
normal_percent = (normal / total * 100) if total > 0 else 0
focus_percent = focus_rate * 100 if isinstance(focus_rate, (int, float)) else 0

render_card(col1, "Tổng lượt phát hiện", total, 100, "blue")
render_card(col2, "Ngủ gật", sleeping, sleep_percent, "red")
render_card(col3, "Bình thường", normal, normal_percent, "green")
render_card(col4, "Tập trung", f"{focus_percent:.1f}%", focus_percent, "blue")

# ================= ALERT =================
if sleeping > 0:
    st.markdown(f"""
    <div class="alert block">
        <div>⚠️ Ghi nhận {sleeping} lượt buồn ngủ hôm nay</div>
        <div class="button">Xem chi tiết</div>
    </div>
    """, unsafe_allow_html=True)

# ================= SO SÁNH =================
if len(df_7d) > 1:
    yesterday = df_7d.iloc[-2]

    if yesterday.get("sleeping", 0) > 0:
        change = (sleeping - yesterday.get("sleeping", 0)) / yesterday.get("sleeping", 1) * 100
    else:
        change = 100 if sleeping > 0 else 0

    st.markdown(f"<div class='block'>📊 So với hôm qua: {change:+.1f}%</div>", unsafe_allow_html=True)

# ================= CHART =================
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    st.markdown('<div class="card block"><div class="title">Xu hướng ngủ gật (7 ngày)</div>', unsafe_allow_html=True)

    if not df_7d.empty:

        df_7d["date_str"] = df_7d["date"].dt.strftime("%d/%m")

        fig = px.bar(
            df_7d,
            x="date_str",
            y="sleeping",
            text="sleeping",
        )

        fig.update_traces(marker_color="#ef4444")

        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font_color="#111827",
            xaxis_title="",
            yaxis_title="Số người ngủ",
            bargap=0.15,
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.write("Chưa có dữ liệu")

    st.markdown('</div>', unsafe_allow_html=True)

# ================= CALENDAR =================
with col_right:
    today = datetime.now()

    st.markdown(f"""
    <div class="card block">
        <div class="title">Hôm nay</div>
        <div style="text-align:center; font-size:40px; font-weight:bold;">
            {today.day}
        </div>
        <div style="text-align:center; color:#6b7280;">
            {today.strftime("%d/%m/%Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)
"""Statistics page — daily trends and summary dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from components.app_sidebar import render_sidebar
from config import API_BASE_URL
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state, get_auth_headers
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Thống kê")

init_session_state()
require_auth()

# ── Styles & Sidebar ────────────────────────────────────────
st.markdown(load_css("styles/statistics.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
hide_sidebar()
render_sidebar(active="statistics")


# ── API ─────────────────────────────────────────────────────
def get_daily(session) -> list:
    """Fetch daily statistics from the backend."""
    try:
        res = session.get(
            f"{API_BASE_URL}/stats/daily",
            headers=get_auth_headers(),
        )
        if res.status_code == 200:
            return res.json()
        if res.status_code == 401:
            st.error("❌ Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại")
            st.stop()
        st.error(f"❌ Lỗi: {res.status_code}")
        return []
    except Exception as exc:
        st.error(f"❌ Lỗi kết nối: {exc}")
        return []


# ── Load Data ───────────────────────────────────────────────
client = st.session_state.client
daily_data = get_daily(client)

if not daily_data:
    st.info("📊 Chưa có dữ liệu thống kê")
    st.stop()

df = pd.DataFrame(daily_data)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ── Filter last 7 days ──────────────────────────────────────
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

# ── Header ──────────────────────────────────────────────────
st.markdown('<div class="title">📊 Thống kê hệ thống</div>', unsafe_allow_html=True)

# ── KPI Cards ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4, gap="large")

sleep_pct = (sleeping / total * 100) if total > 0 else 0
normal_pct = (normal / total * 100) if total > 0 else 0
focus_pct = focus_rate * 100 if isinstance(focus_rate, (int, float)) else 0


def _card(col, title: str, value, percent: float, color: str):
    col.markdown(f"""
    <div class="card">
        <div class="sub">{title}</div>
        <div class="metric">{value}</div>
        <div class="progress">
            <div class="bar {color}" style="width:{percent}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


_card(col1, "Tổng lượt phát hiện", total, 100, "blue")
_card(col2, "Ngủ gật", sleeping, sleep_pct, "red")
_card(col3, "Bình thường", normal, normal_pct, "green")
_card(col4, "Tập trung", f"{focus_pct:.1f}%", focus_pct, "blue")

# ── Alert ───────────────────────────────────────────────────
if sleeping > 0:
    st.markdown(f"""
    <div class="alert block">
        <div>⚠️ Ghi nhận {sleeping} lượt buồn ngủ hôm nay</div>
        <div class="button">Xem chi tiết</div>
    </div>
    """, unsafe_allow_html=True)

# ── Day-over-Day ────────────────────────────────────────────
if len(df_7d) > 1:
    yesterday = df_7d.iloc[-2]
    prev_sleeping = yesterday.get("sleeping", 0)
    change = ((sleeping - prev_sleeping) / prev_sleeping * 100) if prev_sleeping > 0 else (100 if sleeping > 0 else 0)
    st.markdown(
        f"<div class='block'>📊 So với hôm qua: {change:+.1f}%</div>",
        unsafe_allow_html=True,
    )

# ── Chart ───────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1], gap="large")

with col_left:
    st.markdown(
        '<div class="card block"><div class="title">Xu hướng ngủ gật (7 ngày)</div>',
        unsafe_allow_html=True,
    )

    if not df_7d.empty:
        df_7d = df_7d.copy()
        df_7d["date_str"] = df_7d["date"].dt.strftime("%d/%m")

        fig = px.bar(df_7d, x="date_str", y="sleeping", text="sleeping")
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

    st.markdown("</div>", unsafe_allow_html=True)

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
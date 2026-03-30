import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
import requests
import plotly.express as px

st.set_page_config(layout="wide", page_title="Thống kê")

API_URL = "http://localhost:8000"

# ================= API =================
def get_daily():
    try:
        return requests.get(f"{API_URL}/stats/daily").json()
    except:
        return []

# ================= CSS =================
st.markdown("""
<style>
body {
    background-color: #0f172a;
}

.card {
    background: #111827;
    padding: 20px;
    border-radius: 16px;
    color: white;
}

.title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 10px;
}

.metric {
    font-size: 28px;
    font-weight: bold;
}

.sub {
    color: #9ca3af;
    font-size: 14px;
}

.progress {
    height: 6px;
    border-radius: 10px;
    background: #1f2937;
    margin-top: 10px;
}
.bar {
    height: 6px;
    border-radius: 10px;
}

.blue { background: #3b82f6; }
.green { background: #22c55e; }
.red { background: #ef4444; }

.alert {
    background: #7f1d1d;
    padding: 15px;
    border-radius: 12px;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.button {
    background: #ef4444;
    padding: 8px 16px;
    border-radius: 8px;
    color: white;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
from utils.hide_streamlit_sidebar import hide_sidebar
hide_sidebar()

from utils.load_css import load_css
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar(active="statistics")

# ================= LOAD DATA =================
daily_data = get_daily()

if not daily_data:
    st.error("Không có dữ liệu")
    st.stop()

df = pd.DataFrame(daily_data)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ================= FILTER 7 NGÀY =================
seven_days_ago = datetime.now() - timedelta(days=7)
df_7d = df[df["date"] >= seven_days_ago]

latest = df_7d.iloc[-1]

total = int(latest["total"])
sleeping = int(latest["sleeping"])
focus_rate = latest["focus_rate"]
normal = total - sleeping

# ================= HEADER =================
st.markdown('<div class="title">📊 Thống kê hệ thống</div>', unsafe_allow_html=True)

# ================= CARD =================
col1, col2, col3, col4 = st.columns(4)

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
focus_percent = focus_rate * 100


render_card(col1, "Tổng lượt phát hiện", total, 100, "blue")
render_card(col2, "Ngủ gật", sleeping, sleep_percent, "red")
render_card(col3, "Bình thường", normal, normal_percent, "green")
render_card(col4, "Tập trung", f"{focus_percent:.1f}%", focus_percent, "blue")
# ================= ALERT =================
if sleeping > 0:
    st.markdown(f"""
    <div class="alert">
        <div>⚠️ Ghi nhận {sleeping} lượt buồn ngủ hôm nay</div>
        <div class="button">Xem chi tiết</div>
    </div>
    """, unsafe_allow_html=True)

# ================= SO SÁNH HÔM QUA =================
if len(df_7d) > 1:
    yesterday = df_7d.iloc[-2]

    if yesterday["sleeping"] > 0:
        change = (sleeping - yesterday["sleeping"]) / yesterday["sleeping"] * 100
    else:
        change = 100 if sleeping > 0 else 0

    st.write(f"📊 So với hôm qua: {change:+.1f}%")

# ================= CHART + CALENDAR =================
col_left, col_right = st.columns([3, 1])

with col_left:
    st.markdown('<div class="card"><div class="title">Xu hướng ngủ gật (7 ngày)</div>', unsafe_allow_html=True)

    if not df_7d.empty:
        fig = px.bar(
            df_7d,
            x="date",
            y="sleeping",
            text="sleeping",
        )

        fig.update_layout(
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font_color="white",
            xaxis_title="",
            yaxis_title="Số người ngủ",
        )

        fig.update_traces(marker_color="#ef4444")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Chưa có dữ liệu")

    st.markdown('</div>', unsafe_allow_html=True)

# ================= CALENDAR =================
with col_right:
    today = datetime.now()

    st.markdown(f"""
    <div class="card">
        <div class="title">Hôm nay</div>
        <div style="text-align:center; font-size:40px; font-weight:bold;">
            {today.day}
        </div>
        <div style="text-align:center; color:#9ca3af;">
            {today.strftime("%d/%m/%Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ================= AUTO REFRESH =================
#time.sleep(5)
#st.rerun()
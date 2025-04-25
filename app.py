import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.interpolate import UnivariateSpline
import json
import glob
import os
import plotly.graph_objects as go

# Tự động reload sau mỗi 10 phút (600,000ms)
st.set_page_config(page_title="PRIZM Vote Tracker", layout="wide")
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600_000, key="auto_reload")
except:
    pass

st.title("💖 PRIZM Vote Tracker — Top 4 (Auto Update)")

# --- BẢNG GOOGLE SHEET ---
st.subheader("📊 Bảng xếp hạng (Google Sheet)")
try:
    sheet_url = "https://docs.google.com/spreadsheets/d/1T341aZcdJH7pPQSaRt3PwhCOaMEdL8xDSoULMpsfTr4/gviz/tq?tqx=out:csv"
    df_sheet = pd.read_csv(sheet_url)

    df_sheet = df_sheet.dropna(subset=["Votes"])
    df_sheet["Votes"] = (
        df_sheet["Votes"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(int)
    )

    df_top4 = df_sheet.head(4).copy()
    display_cols = ["Rank", "Name", "Votes", "%", "1min", "1h+", "Gap", "Est. Catch"]
    display_cols = [col for col in display_cols if col in df_top4.columns]

    st.dataframe(
        df_top4[display_cols].style.format({"Votes": "{:,}"}),
        use_container_width=True
    )
except Exception as e:
    st.error("Không thể load dữ liệu từ Google Sheet.")
    st.exception(e)

# --- BIỂU ĐỒ VOTE SPEED (PLOTLY) ---
st.subheader("📈 Biểu đồ tốc độ vote (Plotly) — tương tác mượt mà")
try:
    json_files = glob.glob("vote_history_*.json")
    if not json_files:
        st.warning("Không tìm thấy file vote_history_*.json trong thư mục.")
    else:
        latest_file = max(json_files, key=os.path.getmtime)
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        idol_colors = {
            "LEE HYE RI": "dodgerblue",
            "IU": "gold",
            "KIM HYE YOON": "limegreen",
            "HAEWON": "orchid"
        }

        latest_votes = {name: records[-1][1] for name, records in data.items() if records}
        top4_names = sorted(latest_votes.items(), key=lambda x: x[1], reverse=True)[:4]
        top4_names = [name for name, _ in top4_names]

        fig = go.Figure()

        for name in top4_names:
            records = data.get(name, [])
            if len(records) < 2:
                continue

            cleaned = []
            last_time = None
            for t, v in records:
                if t != last_time:
                    cleaned.append((t, v))
                    last_time = t
            records = cleaned

            times = [datetime.fromisoformat(t) for t, _ in records]
            votes = [v for _, v in records]

            speeds = []
            time_points = []
            for i in range(1, len(times)):
                delta_min = (times[i] - times[i-1]).total_seconds() / 60
                delta_votes = votes[i] - votes[i-1]
                speed = delta_votes / delta_min if delta_min > 0 and delta_votes >= 0 else 0
                speeds.append(speed)
                time_points.append(times[i])

            speeds_series = pd.Series(speeds).rolling(window=3, min_periods=1, center=True).mean()
            filtered = [(t.timestamp(), s) for t, s in zip(time_points, speeds_series) if pd.notna(s) and s > 0]
            if len(filtered) < 3:
                continue

            x, y = zip(*filtered)
            spline = UnivariateSpline(x, y, s=len(x)*5)
            x_dense = np.linspace(min(x), max(x), 500)
            y_dense = spline(x_dense)
            x_dense_dt = [datetime.fromtimestamp(ts) for ts in x_dense]

            # Detect gap >15 min
            warning_threshold_min = 15
            cutoff_ts = []
            for i in range(1, len(times)):
                delta = (times[i] - times[i-1]).total_seconds() / 60
                if delta > warning_threshold_min:
                    cutoff_ts.append(times[i].timestamp())

            segments_x = []
            segments_y = []
            segments_hover = []
            segments_color = []

            for i in range(1, len(x_dense)):
                t_prev = x_dense[i-1]
                t_now = x_dense[i]
                is_gap = any(t_prev < cut < t_now for cut in cutoff_ts)
                color = "lightgray" if is_gap else idol_colors.get(name, "gray")
                segments_x.append([x_dense_dt[i-1], x_dense_dt[i]])
                segments_y.append([y_dense[i-1], y_dense[i]])
                segments_hover.append([
                    f"{name}<br>{x_dense_dt[i-1].strftime('%Y-%m-%d %H:%M:%S')}<br>{y_dense[i-1]:,.1f} votes/min",
                    f"{name}<br>{x_dense_dt[i].strftime('%Y-%m-%d %H:%M:%S')}<br>{y_dense[i]:,.1f} votes/min"
                ])
                segments_color.append(color)

            for x_seg, y_seg, hover_seg, color in zip(segments_x, segments_y, segments_hover, segments_color):
                fig.add_trace(go.Scatter(
                    x=x_seg,
                    y=y_seg,
                    mode="lines",
                    line=dict(color=color, width=2),
                    hoverinfo="text",
                    text=hover_seg,
                    name=name if color != "lightgray" else f"{name} (gap)"
                ))

        fig.update_layout(
            title="Vote Speed Over Time — Top 4 (Plotly Interactive)",
            xaxis_title="Time",
            yaxis_title="Votes/min",
            hovermode="x unified",
            legend=dict(title="Idol"),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error("Không thể vẽ biểu đồ Plotly.")
    st.exception(e)

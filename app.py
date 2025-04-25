import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.interpolate import UnivariateSpline
import json
import glob
import os

st.set_page_config(page_title="PRIZM Vote Tracker", layout="wide")
st.title("💖 PRIZM Vote Tracker — Top 4 (Realtime View)")

# --- LOAD BẢNG Từ GOOGLE SHEET ---
st.subheader("📊 Bảng xếp hạng (từ Google Sheet)")
try:
    sheet_url = "https://docs.google.com/spreadsheets/d/1T341aZcdJH7pPQSaRt3PwhCOaMEdL8xDSoULMpsfTr4/gviz/tq?tqx=out:csv"
    df_sheet = pd.read_csv(sheet_url)

    # Loại bỏ dòng thiếu Votes
    df_sheet = df_sheet.dropna(subset=["Votes"])

    # Fix dấu phẩy và convert sang int
    df_sheet["Votes"] = pd.to_numeric(df_sheet["Votes"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype(int)

    # Lấy top 4 theo số vote cao nhất
    df_top4 = df_sheet.sort_values("Votes", ascending=False).head(4).copy()
    df_top4 = df_top4.drop(columns=["Rank"], errors="ignore")
    df_top4.insert(0, "Rank", range(1, len(df_top4) + 1))

    # Hiển thị bảng
    display_cols = ["Rank", "Name", "Votes", "%", "1min", "1h+", "Gap", "Est. Catch"]
    display_cols = [col for col in display_cols if col in df_top4.columns]

    st.dataframe(
        df_top4[display_cols].style.format({"Votes": ":,"}),
        use_container_width=True
    )
except Exception as e:
    st.error("Không thể load dữ liệu từ Google Sheet. Vui lòng kiểm tra link & định dạng bảng.")
    st.exception(e)

# --- LOAD VOTE HISTORY JSON ---
st.subheader("📈 Vote Speed Chart (từ vote_history_*.json)")
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

        # Top 4 theo vote cao nhất hiện tại
        latest_votes = {name: records[-1][1] for name, records in data.items() if records}
        top4_names = sorted(latest_votes.items(), key=lambda x: x[1], reverse=True)[:4]
        top4_names = [name for name, _ in top4_names]

        fig, ax = plt.subplots(figsize=(10, 5))
        for name in top4_names:
            records = data.get(name, [])
            if len(records) < 2:
                continue

            # Bỏ timestamp trùng
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
            for i in range(1, len(records)):
                delta_min = (times[i] - times[i - 1]).total_seconds() / 60
                vote_diff = votes[i] - votes[i - 1]
                speed = vote_diff / delta_min if delta_min > 0 else 0
                speeds.append(speed)
            time_points = times[1:]
            if len(speeds) < 4:
                ax.plot(time_points, speeds, label=name, color=idol_colors.get(name, "gray"))
                continue

            # Spline
            x = [t.timestamp() for t in time_points]
            y = speeds
            spline = UnivariateSpline(x, y, s=len(x)*4)
            x_dense = np.linspace(min(x), max(x), 400)
            y_dense = spline(x_dense)
            x_dense_dt = [datetime.fromtimestamp(ts) for ts in x_dense]

            ax.plot(x_dense_dt, y_dense, label=name, color=idol_colors.get(name, "gray"), linewidth=2)

        ax.set_title("Tốc độ vote (votes/min)")
        ax.set_ylabel("Votes/min")
        ax.set_xlabel("Thời gian")
        ax.legend()
        ax.grid(True)
        fig.autofmt_xdate()
        st.pyplot(fig)
except Exception as e:
    st.error("Không thể vẽ biểu đồ.")
    st.exception(e)

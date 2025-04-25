import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.interpolate import UnivariateSpline
import json
import glob
import os

# Tự động reload sau mỗi 10 phút (600,000ms)
st.set_page_config(page_title="PRIZM Vote Tracker", layout="wide")
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=600000, key="auto_reload")
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

# --- BIỂU ĐỒ VOTE SPEED ---
st.subheader("📈 Biểu đồ tốc độ vote (vote_history_*.json)")
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
            time_points = []
            for i in range(1, len(times)):
                delta = (times[i] - times[i - 1]).total_seconds() / 60
                if delta == 0: continue
                speed = (votes[i] - votes[i - 1]) / delta
                if speed >= 0 and speed < 100000:
                    speeds.append(speed)
                    time_points.append(times[i])

            if len(speeds) < 4:
                ax.plot(time_points, speeds, label=name, color=idol_colors.get(name, "gray"))
                continue

            x = [t.timestamp() for t in time_points]
            spline = UnivariateSpline(x, speeds, s=len(x)*4)
            x_dense = np.linspace(min(x), max(x), 300)
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

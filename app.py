
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import json
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Vote Tracker — Top 4", layout="wide")

st.title("💖 PRIZM Vote Speed Tracker — Top 4 (Realtime View)")

# Tìm file JSON mới nhất
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
json_files = glob.glob(os.path.join(dir_path, "vote_history_*.json"))
if not json_files:
    st.error("Không tìm thấy file vote_history_*.json trong thư mục.")
    st.stop()

latest_file = max(json_files, key=os.path.getmtime)
st.caption(f"Đang xem dữ liệu từ: `{latest_file}`")

with open(latest_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Lấy top 4 theo vote mới nhất
latest_votes = {name: records[-1][1] for name, records in data.items() if records}
top4 = sorted(latest_votes.items(), key=lambda x: x[1], reverse=True)[:4]
top4_names = [name for name, _ in top4]

idol_colors = {
    "LEE HYE RI": "dodgerblue",
    "IU": "gold",
    "KIM HYE YOON": "limegreen",
    "HAEWON": "orchid"
}

fig, ax = plt.subplots(figsize=(10, 5))
for name in top4_names:
    records = data.get(name, [])
    if len(records) < 2:
        continue
    times = [datetime.fromisoformat(t) for t, _ in records]
    votes = [v for _, v in records]
    speeds = []

    for i in range(1, len(records)):
        delta_min = (times[i] - times[i-1]).total_seconds() / 60
        vote_diff = votes[i] - votes[i-1]
        speed = vote_diff / delta_min if delta_min > 0 else 0
        speeds.append(speed)

    time_points = times[1:]
    smoothed = pd.Series(speeds).rolling(window=3, min_periods=1, center=True).mean()
    ax.plot(time_points, smoothed, label=name, color=idol_colors.get(name, 'gray'))

ax.set_title("📈 Vote Speed Over Time")
ax.set_xlabel("Time")
ax.set_ylabel("Votes per Minute")
ax.legend()
ax.grid(True)
fig.autofmt_xdate()

st.pyplot(fig)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.interpolate import UnivariateSpline

# Kết nối Google Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1T341aZcdJH7pPQSaRt3PwhCOaMEdL8xDSoULMpsfTr4/gviz/tq?tqx=out:csv"
df = pd.read_csv(sheet_url)

# Làm sạch dữ liệu và lấy top 4 vote cao nhất
df = df.dropna(subset=["Name", "Votes"])
df["Votes"] = df["Votes"].astype(int)
top4 = df.sort_values(by="Votes", ascending=False).head(4).copy()

# Vẽ biểu đồ vote speed (giả định bạn có cột Time + Speed trong dữ liệu)
# Ở đây chỉ demo line mượt để bạn gắn thêm sau nếu muốn tính speed từ json

idol_colors = {
    "LEE HYE RI": "dodgerblue",
    "IU": "gold",
    "KIM HYE YOON": "limegreen",
    "HAEWON": "orchid"
}

st.title("💖 PRIZM Vote Speed Tracker — Top 4 (Realtime View)")

# Hiển thị bảng
st.subheader("📊 Bảng xếp hạng")
st.dataframe(
    top4[["Name", "Votes"]].style
    .format({"Votes": "{:,}"})
    .applymap(lambda val: f"color: {idol_colors.get(val, 'white')}", subset="Name"),
    use_container_width=True
)

# Placeholder chart mượt (chưa tính speed thật vì chưa có thời gian cụ thể trong sheet)
st.subheader("📈 Biểu đồ vote speed (demo spline mượt)")

# Dữ liệu demo spline (để bạn thay bằng dữ liệu thật sau)
x = np.linspace(0, 10, 20)
for name in top4["Name"]:
    y = np.random.randint(200, 700, size=20)
    spline = UnivariateSpline(x, y, s=50)
    plt.plot(x, spline(x), label=name, color=idol_colors.get(name, None))
plt.xlabel("Time (demo)")
plt.ylabel("Votes per min (demo)")
plt.legend()
st.pyplot(plt)

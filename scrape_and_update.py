import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# --- SETUP GOOGLE SHEET ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Mở Google Sheet
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1T341aZcdJH7pPQSaRt3PwhCOaMEdL8xDSoULMpsfTr4'
worksheet = client.open_by_url(spreadsheet_url).sheet1

# --- SCRAPE PRIZM ---
def scrape_top4_female():
    url = "https://global.prizm.co.kr/vote"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Tìm bảng vote
    vote_items = soup.select(".vote_list > li")

    results = []
    for item in vote_items:
        name = item.select_one(".info > .name").get_text(strip=True)
        votes = item.select_one(".info > .vote").get_text(strip=True).replace(",", "").replace(".", "")

        # Bỏ qua những tên nam hoặc blacklist nếu cần
        blacklist = ["BYEON WOO SEOK", "KIM SEON HO", "NAM JOO HYUK"]  # tùy bạn bổ sung
        if name.upper() in blacklist:
            continue

        try:
            votes = int(votes)
        except:
            continue

        results.append((name, votes))

    # Lấy top 4 theo số vote
    top4 = sorted(results, key=lambda x: x[1], reverse=True)[:4]

    df = pd.DataFrame(top4, columns=["Name", "Votes"])
    return df

# --- UPDATE SHEET ---
def update_sheet(df):
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("✅ Update thành công vào Google Sheet!")

# --- MAIN LOOP ---
if __name__ == "__main__":
    while True:
        try:
            df = scrape_top4_female()
            update_sheet(df)
        except Exception as e:
            print("❌ Lỗi:", e)

        # Chờ 5 phút rồi scrape lại
        time.sleep(300)

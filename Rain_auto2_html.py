# -*- coding: utf-8 -*-
"""
Created on Thu Mar 12 14:53:16 2026

@author: User
"""

import requests
import pandas as pd
#import schedule
#import time
import urllib3
import os
from datetime import datetime, timedelta # 確保最上面有 import timedelta

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 參數設定 ---
# 從 GitHub Secrets 讀取金鑰，如果讀不到就維持原本的
API_KEY = os.getenv("CWA_API_KEY", "你的備用金鑰")
TARGET_FILE = "index.html" # 確保檔名是 index.html，GitHub Pages 才能讀取
#API_KEY = "CWA-D248BB38-82C9-47CB-865F-A5ADEFF3D7B3"
INTERVAL_MINUTES = 10         
#TARGET_FILE = "Rain_auto.html"
TARGET_COUNTIES = ["苗栗縣", "臺中市", "南投縣", "彰化縣"]

def fetch_and_save_to_html():
    # 修正為台灣時間 (UTC+8)
    tw_time = datetime.now() + timedelta(hours=8)
    current_time = tw_time.strftime("%Y-%m-%d %H:%M:%S")
    refresh_seconds = INTERVAL_MINUTES * 60
    
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={API_KEY}"
    
    try:
        response = requests.get(url, verify=False)
        data = response.json()
        stations = data["records"]["Station"]
        extracted_data = []
        
        for st in stations:
            county = st["GeoInfo"]["CountyName"]
            if county in TARGET_COUNTIES:
                elements = st["RainfallElement"]
                
                # 取得各時段數值
                rain_now = float(elements["Now"]["Precipitation"])
                rain_10m = float(elements["Past10Min"]["Precipitation"])
                rain_1h = float(elements["Past1hr"]["Precipitation"])
                rain_3h = float(elements["Past3hr"]["Precipitation"])
                rain_6h = float(elements["Past6Hr"]["Precipitation"])
                rain_12h = float(elements["Past12hr"]["Precipitation"])
                rain_24h = float(elements["Past24hr"]["Precipitation"])
                rain_2d = float(elements["Past2days"]["Precipitation"])
                rain_3d = float(elements["Past3days"]["Precipitation"])
                
                # 顏色判定樣式 (放在屬性中，讓 DataTables 排序時仍能抓到數值)
                c_1h = 'style="background-color: #ff4d4d; color: white; font-weight: bold;"' if rain_1h >= 40 else ""
                c_3h = 'style="background-color: #9b59b6; color: white; font-weight: bold;"' if rain_3h >= 100 else ""
                
                extracted_data.append({
                    "縣市": county,
                    "行政區": st["GeoInfo"]["TownName"],
                    "站名": st["StationName"],
                    "現在": rain_now,
                    "10m": rain_10m,
                    "1h": f'<td {c_1h}>{rain_1h}</td>',
                    "3h": f'<td {c_3h}>{rain_3h}</td>',
                    "6h": rain_6h,
                    "12h": rain_12h,
                    "24h": rain_24h,
                    "2d": rain_2d,
                    "3d": rain_3d
                })
        
        df = pd.DataFrame(extracted_data)
        # 生成 HTML 表格，給它一個 id 方便 JavaScript 呼叫
        table_html = df.to_html(index=False, escape=False, table_id="rainTable", classes='display nowrap')
        table_html = table_html.replace('<td><td', '<td').replace('</td></td>', '</td>')

        # --- HTML 模板 (加入 DataTables 資源) ---
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="{refresh_seconds}">
            <title>智慧雨量監測儀表板</title>
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
            <style>
                body {{ font-family: 'Microsoft JhengHei', sans-serif; margin: 20px; background-color: #f8f9fa; }}
                .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                h2 {{ color: #2c3e50; margin-bottom: 5px; }}
                .info {{ font-size: 0.85em; color: #666; margin-bottom: 20px; }}
                th {{ background-color: #34495e !important; color: white !important; text-align: center !important; }}
                td {{ text-align: center !important; }}
                /* 搜尋框樣式優化 */
                .dataTables_filter input {{ border: 1px solid #ddd; border-radius: 4px; padding: 5px; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🌧️ 中台灣智慧雨量監測系統</h2>
                <p class="info">最後更新：{current_time} | 網頁每 {INTERVAL_MINUTES} 分鐘自動刷新</p>
                
                {table_html}
            </div>

            <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
            <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
            <script>
                $(document).ready(function() {{
                    $('#rainTable').DataTable({{
                        "pageLength": 50,  // 預設顯示 50 筆
                        "order": [[ 0, "asc" ]], // 預設依縣市排序
                        "language": {{
                            "search": "🔍 搜尋站名/縣市：",
                            "lengthMenu": "顯示 _MENU_ 筆資料",
                            "info": "顯示第 _START_ 至 _END_ 筆，共 _TOTAL_ 筆",
                            "paginate": {{
                                "next": "下一頁",
                                "previous": "上一頁"
                            }}
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[{current_time}] 具備搜尋與排序功能的網頁已更新。")

    except Exception as e:
        print(f"發生錯誤: {e}")

# 排程與執行
#schedule.every(INTERVAL_MINUTES).minutes.do(fetch_and_save_to_html)
if __name__ == "__main__":
    fetch_and_save_to_html()

#while True:
#    schedule.run_pending()
#    time.sleep(1)

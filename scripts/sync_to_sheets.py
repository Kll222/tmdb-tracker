import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 读取 Google 凭证
creds_json = os.environ["GOOGLE_CREDENTIALS"]
creds_dict = json.loads(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 打开 Google Sheet
spreadsheet_id = os.environ["SPREADSHEET_ID"]
sheet = client.open_by_key(spreadsheet_id).sheet1

# 读取 JSON
with open("output/output.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 清空原表格
sheet.clear()

# 写入表头和内容
if data:
    headers = list(data[0].keys())
    sheet.append_row(headers)

    rows = [[str(item.get(h, "")) for h in headers] for item in data]
    sheet.append_rows(rows)

import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import unquote

API_KEY = unquote(os.environ["DATA_API_KEY"])
TG_TOKEN = os.environ["TG_TOKEN"]
TG_CHAT_ID = os.environ["TG_CHAT_ID"]

SEEN_FILE = "seen_ids.txt"
URL = "http://apis.data.go.kr/1312000/PublicEmpmnInfoService/getPublicEmpmnInfoList"

if os.path.exists(SEEN_FILE):
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        seen_ids = set(line.strip() for line in f if line.strip())
else:
    seen_ids = set()

params = {
    "serviceKey": API_KEY,
    "pageNo": "1",
    "numOfRows": "100",
}

response = requests.get(URL, params=params, timeout=15)
root = ET.fromstring(response.text)

new_alerts = []

for item in root.findall(".//item"):
    empmn_sn = item.findtext("empmnSn", "").strip()
    title = item.findtext("empmnSj", "").strip()
    org_name = item.findtext("insttNm", "").strip()
    emp_type = item.findtext("empmnSeNm", "").strip()
    job_type = item.findtext("occpNm", "").strip()
    work_area = item.findtext("workAreaNm", "").strip()
    start_dt = item.findtext("rceptBgnde", "").strip()
    end_dt = item.findtext("rceptEndde", "").strip()

    if not empmn_sn or empmn_sn in seen_ids:
        continue

    seen_ids.add(empmn_sn)

    combined_text = f"{title} {job_type}"
    exclude_keywords = ["공무직", "기간제", "임기제", "시간선택제", "대체", "청원경찰"]

    if "운전" in combined_text and not any(ex in combined_text for ex in exclude_keywords):
        link = f"https://www.gojobs.go.kr/apmView.do?empmnSn={empmn_sn}"
        msg = (
            f"📢 <b>[나라일터 운전직 새 공고]</b>\n\n"
            f"• <b>기관:</b> {org_name}\n"
            f"• <b>공고명:</b> {title}\n"
            f"• <b>구분/지역:</b> {emp_type} / {work_area}\n"
            f"• <b>접수기간:</b> {start_dt} ~ {end_dt}\n"
            f"• <a href='{link}'>공고 바로가기</a>"
        )
        new_alerts.append(msg)

for alert in new_alerts:
    tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(
        tg_url,
        data={
            "chat_id": TG_CHAT_ID,
            "text": alert,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

with open(SEEN_FILE, "w", encoding="utf-8") as f:
    for sid in sorted(seen_ids):
        f.write(sid + "\n")

print(f"체크 완료 / 신규 발송: {len(new_alerts)}건")

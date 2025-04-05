import os
import json
import requests
from datetime import datetime

# ✅ API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
LEAGUE_ID = 39
SEASON = 2024
HEADERS = {"x-apisports-key": API_KEY}


# ✅ 저장할 폴더 경로 설정
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))  # 현재 파일 경로 기준
DATA_DIR = os.path.join(REPO_ROOT, "..", "data")  # `data/` 폴더가 한 단계 위에 있어야 함
os.makedirs(DATA_DIR, exist_ok=True)  # ✅ 폴더가 없으면 생성
print(f"📂 데이터 폴더 경로: {DATA_DIR}")

# ✅ 팀 ID
TEAM_IDS = {
    "Arsenal": 42, "Aston Villa": 66, "Bournemouth": 35, "Brentford": 55,
    "Brighton": 51, "Chelsea": 49, "Crystal Palace": 52, "Everton": 45,
    "Fulham": 36, "Ipswich": 2636, "Liverpool": 40, "Luton": 1359,
    "Manchester City": 50, "Manchester United": 33, "Newcastle": 34,
    "Nottingham Forest": 65, "Sheffield Utd": 62, "Southampton": 41,
    "Tottenham": 47, "West Ham": 48
}

# ✅ API 호출 함수
def fetch_data(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
    except Exception as e:
        print(f"❌ API 오류: {e}")
        return []

# ✅ 팀별 종료 경기 중 마지막 경기만 추출
latest_games = {}
for team_name, team_id in TEAM_IDS.items():
    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&team={team_id}"
    fixtures = fetch_data(url)

    # 종료된 경기만 필터링
    finished = [f for f in fixtures if f["fixture"]["status"]["short"] == "FT"]
    if not finished:
        continue

    # 가장 마지막 날짜의 경기 선택
    finished.sort(key=lambda x: x["fixture"]["date"], reverse=True)
    last_game = finished[0]

    # 홈팀 기준 중복 제거
    home_team = last_game["teams"]["home"]["name"]
    if home_team not in latest_games:
        latest_games[home_team] = last_game

# ✅ JSON 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(list(latest_games.values()), f, ensure_ascii=False, indent=2)

print(f"✅ 2. 저장 완료: {OUTPUT_FILE}")

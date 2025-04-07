import os
import json
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser

# ✅ API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
LEAGUE_ID = 39
SEASON = 2024
HEADERS = {"x-apisports-key": API_KEY}

# ✅ 저장할 폴더 경로 설정
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))  # 현재 파일 기준 경로
DATA_DIR = os.path.join(REPO_ROOT, "..", "data")        # ../data 폴더 경로
os.makedirs(DATA_DIR, exist_ok=True)                    # 없으면 생성

# ✅ 저장 파일 경로 지정
save_path = os.path.join(DATA_DIR, "premier_upcoming_0409_0430.json")
print(f"📂 저장 경로: {save_path}")

# ✅ 한글 팀명 매핑
TEAM_NAME_MAPPING = {
    "Nottingham Forest": "노팅엄 포레스트",
    "Manchester City": "맨 시티",
    "Liverpool": "리버풀",
    "Southampton": "사우샘프턴",
    "Brighton": "브라이턴",
    "Fulham": "풀럼",
    "Crystal Palace": "크리스털 팰리스",
    "Ipswich": "입스위치",
    "Brentford": "브렌트퍼드",
    "Aston Villa": "애스턴 빌라",
    "Wolves": "울브스",
    "Everton": "에버턴",
    "Tottenham": "토트넘",
    "Bournemouth": "본머스",
    "Chelsea": "첼시",
    "Leicester": "레스터 시티",
    "Manchester United": "맨유",
    "Arsenal": "아스널",
    "West Ham": "웨스트 햄",
    "Newcastle": "뉴캐슬"
}

# ✅ 팀 ID
TEAM_IDS = {
    "Arsenal": 42, "Aston Villa": 66, "Bournemouth": 35, "Brentford": 55,
    "Brighton": 51, "Chelsea": 49, "Crystal Palace": 52, "Everton": 45,
    "Fulham": 36, "Ipswich": 2636, "Liverpool": 40, "Luton": 1359,
    "Manchester City": 50, "Manchester United": 33, "Newcastle": 34,
    "Nottingham Forest": 65, "Sheffield Utd": 62, "Southampton": 41,
    "Tottenham": 47, "West Ham": 48
}

# ✅ 공통 함수
def fetch_data(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return []

# ✅ 출력 객체 초기화
output = {
    "리그명": "프리미어리그",
    "시즌": SEASON,
    "순위표": [],
    "경기일정": [],
    "팀별 최근 경기": []
}

# ✅ 순위표 수집
standings_url = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"
standings = fetch_data(standings_url)

if standings:
    for item in standings[0]["league"]["standings"][0]:
        name = item["team"]["name"]
        output["순위표"].append({
            "순위": item["rank"],
            "팀명": TEAM_NAME_MAPPING.get(name, name),
            "경기수": item["all"]["played"],
            "승": item["all"]["win"],
            "무": item["all"]["draw"],
            "패": item["all"]["lose"],
            "승점": item["points"],
            "득점": item["all"]["goals"]["for"],
            "실점": item["all"]["goals"]["against"],
            "득실차": item["goalsDiff"]
        })

# ✅ 최근 경기 1건 수집
latest_url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&status=FT"
latest_matches = fetch_data(latest_url)

if latest_matches:
    latest = sorted(latest_matches, key=lambda x: x["fixture"]["date"], reverse=True)[0]
    output["최근 경기"] = {
        "날짜": latest["fixture"]["date"][:10],
        "홈팀": TEAM_NAME_MAPPING.get(latest["teams"]["home"]["name"], latest["teams"]["home"]["name"]),
        "스코어": f"{latest['goals']['home']} - {latest['goals']['away']}",
        "원정팀": TEAM_NAME_MAPPING.get(latest["teams"]["away"]["name"], latest["teams"]["away"]["name"])
    }

# ✅ 경기 일정 (4월 9일 ~ 4월 30일)
start_date = "2025-04-09"
end_date = "2025-04-30"
schedules_url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&from={start_date}&to={end_date}"
schedules = fetch_data(schedules_url)

KST = timezone(timedelta(hours=9))
base_url = "https://chatboy.tistory.com/"
start_post_id = 551

for i, match in enumerate(schedules):
    fixture = match.get("fixture", {})
    teams = match.get("teams", {})

    if fixture.get("id") == 1208357:
        continue  # ❌ 특정 경기 제외

    utc_time = parser.isoparse(fixture.get("date"))
    kst_time_str = utc_time.astimezone(KST).strftime("%Y-%m-%d %H:%M")

    output["경기일정"].append({
        "경기 ID": fixture.get("id"),
        "날짜": kst_time_str,
        "홈팀": TEAM_NAME_MAPPING.get(teams.get("home", {}).get("name", ""), "N/A"),
        "원정팀": TEAM_NAME_MAPPING.get(teams.get("away", {}).get("name", ""), "N/A"),
        "장소": fixture.get("venue", {}).get("name", "N/A"),
        "blog_url": f"{base_url}{start_post_id + i}",
        "home_blog_url": base_url,  # 🔗 홈팀용
        "away_blog_url": base_url   # 🔗 원정팀용
    })

# ✅ 각 팀별 최근 종료된 경기 1건 수집
team_latest_matches = []

for team_en, team_id in TEAM_IDS.items():
    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&team={team_id}"
    fixtures = fetch_data(url)

    finished = [f for f in fixtures if f["fixture"]["status"]["short"] == "FT"]
    if not finished:
        continue

    latest_game = sorted(finished, key=lambda x: x["fixture"]["date"], reverse=True)[0]
    fixture = latest_game["fixture"]
    teams = latest_game["teams"]
    goals = latest_game["goals"]
    date_kst = parser.isoparse(fixture["date"]).astimezone(KST).strftime("%Y-%m-%d %H:%M")

    team_latest_matches.append({
        "팀": TEAM_NAME_MAPPING.get(team_en, team_en),
        "날짜": date_kst,
        "홈팀": TEAM_NAME_MAPPING.get(teams["home"]["name"], teams["home"]["name"]),
        "원정팀": TEAM_NAME_MAPPING.get(teams["away"]["name"], teams["away"]["name"]),
        "스코어": f"{goals['home']} - {goals['away']}"
    })

output["팀별 최근 경기"] = team_latest_matches

# ✅ 저장
with open(save_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=4)

print(f"✅ 모든 데이터 통합 저장 완료: {save_path}")

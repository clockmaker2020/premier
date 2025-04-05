import os
import json
import requests
from datetime import datetime, timedelta, timezone


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


# ✅ 팀명 변환 (한글)
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
    "Newcastle": "뉴캐슬",
    "Luton": "루턴 타운",
    "Sheffield Utd": "셰필드 유나이티드"
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

# ✅ API 요청 함수
def fetch_data(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json().get("response", [])
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return []

# ✅ 순위 데이터 수집
standings_url = f"https://v3.football.api-sports.io/standings?league={LEAGUE_ID}&season={SEASON}"
standings = fetch_data(standings_url)

output = {
    "리그명": "프리미어리그",
    "시즌": SEASON,
    "순위표": []
}

if standings:
    for item in standings[0]["league"]["standings"][0]:
        eng_name = item["team"]["name"]
        kor_name = TEAM_NAME_MAPPING.get(eng_name, eng_name)

        team_entry = {
            "순위": item["rank"],
            "팀명": kor_name,
            "경기수": item["all"]["played"],
            "승": item["all"]["win"],
            "무": item["all"]["draw"],
            "패": item["all"]["lose"],
            "승점": item["points"],
            "득점": item["all"]["goals"]["for"],
            "실점": item["all"]["goals"]["against"],
            "득실차": item["goalsDiff"]
        }

        output["순위표"].append(team_entry)

# ✅ 최근 경기 1건
fixtures_url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&status=FT"
matches = fetch_data(fixtures_url)

if matches:
    latest = sorted(matches, key=lambda x: x["fixture"]["date"], reverse=True)[0]
    date = latest["fixture"]["date"][:10]
    home = TEAM_NAME_MAPPING.get(latest["teams"]["home"]["name"], latest["teams"]["home"]["name"])
    away = TEAM_NAME_MAPPING.get(latest["teams"]["away"]["name"], latest["teams"]["away"]["name"])
    score = f"{latest['goals']['home']} - {latest['goals']['away']}"

    output["최근 경기"] = {
        "날짜": date,
        "홈팀": home,
        "스코어": score,
        "원정팀": away
    }

    print(f"✅ 최근 경기 추가: {date} | {home} {score} {away}")
else:
    print("⚠️ 최근 종료 경기를 찾을 수 없습니다.")

# ✅ 팀별 마지막 종료 경기 (홈팀 기준 중복 제거)
latest_games = {}
for team_name, team_id in TEAM_IDS.items():
    url = f"https://v3.football.api-sports.io/fixtures?league={LEAGUE_ID}&season={SEASON}&team={team_id}"
    fixtures = fetch_data(url)

    finished = [f for f in fixtures if f["fixture"]["status"]["short"] == "FT"]
    if not finished:
        continue

    finished.sort(key=lambda x: x["fixture"]["date"], reverse=True)
    last_game = finished[0]

    home_team = last_game["teams"]["home"]["name"]
    if home_team not in latest_games:
        latest_games[home_team] = last_game

# ✅ 한글 이름 적용 및 결과 저장
converted_games = []

# ✅ 팀명 → 순위 매핑 생성
team_rank_map = {team["팀명"]: team["순위"] for team in output["순위표"]}

# ✅ KST 타임존 정의 (UTC+9)
KST = timezone(timedelta(hours=9))

# ✅ 필터 범위 (한국시간 기준, offset-aware)
april_start = datetime(2025, 4, 1, tzinfo=KST)
april_end = datetime(2025, 4, 30, 23, 59, 59, tzinfo=KST)



for game in latest_games.values():
    # UTC -> 한국시간
    fixture_datetime_utc = datetime.fromisoformat(game["fixture"]["date"].replace("Z", "+00:00"))
    fixture_datetime_kst = fixture_datetime_utc + timedelta(hours=9)

    # 범위 필터링
    if not (april_start <= fixture_datetime_kst <= april_end):
        continue

    fixture_date = fixture_datetime_kst.strftime("%Y-%m-%d")
    fixture_time = fixture_datetime_kst.strftime("%H:%M")
    
    home = TEAM_NAME_MAPPING.get(game["teams"]["home"]["name"], game["teams"]["home"]["name"])
    away = TEAM_NAME_MAPPING.get(game["teams"]["away"]["name"], game["teams"]["away"]["name"])
    score = f"{game['goals']['home']} - {game['goals']['away']}"


    converted_games.append({
        "date": fixture_date,
        "time": fixture_time,
        "home_team": home,
        "away_team": away,
        "score": score,
        "home_team_rank": team_rank_map.get(home),
        "away_team_rank": team_rank_map.get(away),
        "status": "Match Finished",
        "blog_url": f"https://example.com/preview/{home.lower().replace(' ', '-')}-vs-{away.lower().replace(' ', '-')}",
        "home_recent_url": f"https://example.com/recent/{home.lower().replace(' ', '-')}",
        "away_recent_url": f"https://example.com/recent/{away.lower().replace(' ', '-')}"
    })

output["팀별 최종 경기"] = converted_games
output["matches"] = converted_games  # ✅ JS 렌더링 호환용 추가
print(f"✅ 팀별 최종 경기 {len(converted_games)}건 추가 완료")

# ✅ 저장 경로 지정
filename = f"premier_april_until_0408.json"
save_path = os.path.join(DATA_DIR, filename)

# ✅ 최종 저장
try:
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print(f"✅ 최종 JSON 저장 완료: {save_path}")
except Exception as e:
    print(f"❌ 저장 실패: {e}")



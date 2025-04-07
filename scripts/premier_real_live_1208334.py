import os
import json
import requests
from datetime import datetime, timedelta

# ✅ START: 프로그램 시작
print("🚀 START: 경기 데이터 수집 시작")

# ✅ 현재 작업 디렉토리 출력
print(f"📂 현재 작업 디렉토리: {os.getcwd()}")

# ✅ API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
HEADERS = {"x-apisports-key": API_KEY}

# ✅ 저장할 폴더 경로 설정
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))  # 현재 파일 경로 기준
DATA_DIR = os.path.join(REPO_ROOT, "..", "data")  # data/ 폴더가 한 단계 위에 있어야 함
os.makedirs(DATA_DIR, exist_ok=True)  # ✅ 폴더가 없으면 생성

print(f"📂 데이터 폴더 경로: {DATA_DIR}")

# ✅ API 요청 함수
def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API 요청 실패: {e}")
        return []

# ✅ JSON 저장 함수
def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ✅ 경기 시작 시간 변환 및 저장
def save_match_start_time(match_id, start_time, start_time_kst):
    file_path = os.path.join(DATA_DIR, f"match_{match_id}_start.json")

    try:
        # ✅ API에서 받은 ISO 8601 날짜 형식을 변환
        utc_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))  
        start_time_kst = utc_time + timedelta(hours=9)  
        start_time_kst_str = start_time_kst.strftime("%Y-%m-%d %H:%M:%S")  

        # ✅ 경기 시작 10분 전 시간 계산
        start_time_850_kst = (start_time_kst - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(f"⚠️ 시간 변환 실패: {start_time}")
        start_time_kst_str = "UNKNOWN"
        start_time_850_kst = "UNKNOWN"

    data = {
        "start_time": start_time,  
        "start_time_kst": start_time_kst_str,  
        "start_time_850_kst": start_time_850_kst  
    }

    save_json(file_path, data)
    print(f"✅ 경기 시작 시간 저장 완료: {file_path}")


# ✅ 한국식 배당률 JSON 저장 함수 (경기 ID 기반 저장)
def save_odds_json(match_id, odds_data):
    file_name = f"pre_bet_{match_id}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    if odds_data:
        save_json(file_path, odds_data)
        print(f"✅ 경기 ID {match_id} 배당률 데이터 저장 완료: {file_path}")
    else:
        print(f"⚠️ 경기 ID {match_id} 배당률 데이터가 없습니다. 빈 JSON 파일을 생성합니다.")
        save_json(file_path, [{"배팅사": "N/A", "배당률": "데이터 없음"}])

# ✅ 한국식 배당률 데이터 변환 함수 (승무패 + 오버/언더 2.5) - 3개 배팅사만 필터링
def process_odds_data(odds_details):
    if not odds_details:
        return [{"배팅사": "N/A", "배당률": "데이터 없음"}]

    # ✅ 사용할 배팅사 리스트
    SELECTED_BOOKMAKERS = {"Bet365", "William Hill", "Betway"}

    odds_data = []
    for fixture in odds_details:
        fixture_id = fixture.get("fixture", {}).get("id", "N/A")
        bookmakers = fixture.get("bookmakers", [])

        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get("name", "N/A")
            if bookmaker_name not in SELECTED_BOOKMAKERS:
                continue  # ✅ 3개 배팅사가 아니면 건너뜀

            bets = bookmaker.get("bets", [])
            bet_dict = {"배팅사": bookmaker_name, "승무패": {}, "오버언더": {}}

            for bet in bets:
                bet_name = bet.get("name", "N/A")
                values = bet.get("values", [])

                for odd in values:
                    if bet_name == "Match Winner":
                        if odd["value"] == "Home":
                            bet_dict["승무패"]["홈"] = odd["odd"]
                        elif odd["value"] == "Draw":
                            bet_dict["승무패"]["무"] = odd["odd"]
                        elif odd["value"] == "Away":
                            bet_dict["승무패"]["원정"] = odd["odd"]
                    elif bet_name == "Over/Under 2.5":
                        if odd["value"] == "Over":
                            bet_dict["오버언더"]["오버 2.5"] = odd["odd"]
                        elif odd["value"] == "Under":
                            bet_dict["오버언더"]["언더 2.5"] = odd["odd"]

            odds_data.append(bet_dict)

    return odds_data if odds_data else [{"배팅사": "N/A", "배당률": "데이터 없음"}]

# ✅ 2. 종합 정보
# ✅ 팀 순위 등 정보 (승률, 득실차, 평균 포함)
def fetch_team_rank_full(league_id, season, team_name):
    url = f"https://v3.football.api-sports.io/standings?league={league_id}&season={season}"
    standings_data = fetch_data(url)

    for league in standings_data:
        for group in league.get("league", {}).get("standings", []):
            for team in group:
                if team["team"]["name"].lower() == team_name.lower():
                    all_stats = team.get("all", {})
                    home_stats = team.get("home", {})
                    away_stats = team.get("away", {})
                    form = team.get("form", "N/A")

                    played = all_stats.get("played", 0)
                    win = all_stats.get("win", 0)
                    draw = all_stats.get("draw", 0)
                    lose = all_stats.get("lose", 0)
                    goals_for = all_stats.get("goals", {}).get("for", 0)
                    goals_against = all_stats.get("goals", {}).get("against", 0)
                    goal_diff = goals_for - goals_against

                    return {
                        "팀": team["team"]["name"],
                        "순위": team["rank"],
                        "승점": team["points"],
                        "경기수": played,
                        "승/무/패": f"{win}/{draw}/{lose}",
                        "승률": f"{(win / played * 100):.1f}%" if played else "N/A",
                        "득/실": f"{goals_for} / {goals_against}",
                        "득실차": goal_diff,
                        "평균 득점": round(goals_for / played, 2) if played else 0.0,
                        "평균 실점": round(goals_against / played, 2) if played else 0.0,
                        "최근 5경기": form,
                        "홈 성적": f"{home_stats.get('win', 0)}승 {home_stats.get('draw', 0)}무 {home_stats.get('lose', 0)}패",
                        "원정 성적": f"{away_stats.get('win', 0)}승 {away_stats.get('draw', 0)}무 {away_stats.get('lose', 0)}패"
                    }

    return {"팀": team_name, "순위": "N/A"}

# ✅ 경기 데이터 저장 함수
def save_json_with_match_id(match_id, data):
    file_name = f"real_live_{match_id}.json"
    file_path = os.path.join(DATA_DIR, file_name)
    save_json(file_path, data)
    print(f"✅ 경기 데이터 저장 완료: {file_path}")

# ✅ 경기 데이터 가져오기
def get_match_data(match_id):
    print(f"🔍 경기 데이터 수집 시작: Match ID = {match_id}")

    # 📌 API 엔드포인트 설정
    detail_url = f"https://v3.football.api-sports.io/fixtures?id={match_id}"
    odds_url = f"https://v3.football.api-sports.io/odds?fixture={match_id}"  # 배당률 데이터 요청

    # 📌 API 데이터 요청
    match_details = fetch_data(detail_url)
    odds_details = fetch_data(odds_url)

    if not match_details:
        print("⚠️ 경기 데이터를 찾을 수 없습니다.")
        return "NO_DATA"
        
    match_data = match_details[0]
    league_info = match_data.get("league", {})
    fixture_info = match_data.get("fixture", {})
    league_info = match_data.get("league", {})
    teams = match_data.get("teams", {})
    events = match_data.get("events", [])
    stats = match_data.get("statistics", [])
    lineups = match_data.get("lineups", [])
    players = match_data.get("players", [])

    # ✅ 리그 정보로 팀 순위 조회용 정보 준비
    league_id = league_info.get("id", 39)
    season = league_info.get("season", 2024)
    home_team_name = teams.get("home", {}).get("name", "")
    away_team_name = teams.get("away", {}).get("name", "")

    # ✅ 팀 순위 정보 호출
    home_rank = fetch_team_rank_full(league_id, season, home_team_name)
    away_rank = fetch_team_rank_full(league_id, season, away_team_name)

    # ✅ 배당률 데이터 저장
    odds_data = process_odds_data(odds_details)
    save_odds_json(match_id, odds_data)

    # ✅ 경기 시작 시간 처리
    match_start_time = fixture_info.get("date", "UNKNOWN")
    save_match_start_time(match_id, match_start_time, match_start_time)

    start_time_file = os.path.join(DATA_DIR, f"match_{match_id}_start.json")
    try:
        with open(start_time_file, "r", encoding="utf-8") as f:
            start_time_data = json.load(f)
            match_start_time_kst = start_time_data.get("start_time_kst", "UNKNOWN")
    except FileNotFoundError:
        match_start_time_kst = "UNKNOWN"

    match_status = fixture_info.get("status", {}).get("long", "UNKNOWN")

    # ✅ JSON 구성
    match_json = {
        "경기 ID": match_id,
        "경기 날짜": match_start_time_kst,
        "경기장": fixture_info.get("venue", {}).get("name", "N/A"),
        "도시": fixture_info.get("venue", {}).get("city", "N/A"),
        "경기 상태": match_status,
        "리그": league_info.get("name", "N/A"),
        "라운드": league_info.get("round", "N/A"),
        "심판": fixture_info.get("referee", "N/A"),
        "관중 수": fixture_info.get("attendance", "N/A"),
        "팀 정보": {
            "홈팀": {
                "이름": home_team_name,
                "로고": teams.get("home", {}).get("logo", "N/A")
            },
            "원정팀": {
                "이름": away_team_name,
                "로고": teams.get("away", {}).get("logo", "N/A")
            }
        },
        "팀 순위": {
            "홈팀": home_rank,
            "원정팀": away_rank
        },
        "현재 점수": f"{match_data.get('goals', {}).get('home', 0)} - {match_data.get('goals', {}).get('away', 0)}",
        "득점 기록": [
            {
                "시간": event["time"]["elapsed"],
                "선수": event["player"]["name"],
                "팀": event["team"]["name"]
            }
            for event in events if event["type"] == "Goal"
        ],
        "경기 이벤트": [
            {
                "이벤트 종류": event["type"],
                "선수": event.get("player", {}).get("name", "N/A"),
                "팀": event.get("team", {}).get("name", "N/A"),
                "시간": event.get("time", {}).get("elapsed", "N/A")
            }
            for event in events
        ],
        "경기 통계": [
            {
                "팀": stat.get("team", {}).get("name", "N/A"),
                "항목": value.get("type", "N/A"),
                "수치": value.get("value", "N/A")
            }
            for stat in stats if isinstance(stat, dict)
            for value in stat.get("statistics", [])
        ] if stats else [{"팀": "N/A", "항목": "N/A", "수치": "N/A"}],
        "라인업": [
            {
                "팀": lineup["team"]["name"],
                "포메이션": lineup["formation"],
                "선발 선수": [p["player"]["name"] for p in lineup["startXI"]],
                "교체 선수": [p["player"]["name"] for p in lineup["substitutes"]]
            }
            for lineup in lineups
        ],
        "선수별 통계": [
            {
                "선수": player.get("player", {}).get("name", "N/A"),
                "팀": team.get("team", {}).get("name", "N/A"),
                "포지션": player.get("statistics", [{}])[0].get("games", {}).get("position", "N/A"),
                "스탯": player.get("statistics", [])
            }
            for team in players if isinstance(team, dict)
            for player in team.get("players", [])
        ]
    }

    # ✅ 저장
    save_json_with_match_id(match_id, match_json)
    return "SAVED"


# ✅ 실행
if __name__ == "__main__":
    match_id = 1208334
    print(f"🎯 실행 시작: Match ID = {match_id}")
    result = get_match_data(match_id)
    print(f"✅ 실행 결과: {result}")

# ✅ END: 프로그램 종료
print("🏁 END: 경기 데이터 수집 완료")

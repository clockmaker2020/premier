import os
import json
import requests
from datetime import datetime, timedelta

# 1. START: 프로그램 시작
print("🚀 START: 경기 데이터 수집 시작")

# 2. 현재 작업 디렉토리 출력
print(f"📂 현재 작업 디렉토리: {os.getcwd()}")

# 3. API 설정
API_KEY = "0776a35eb1067086efe59bb7f93c6498"
HEADERS = {"x-apisports-key": API_KEY}

# 4.1. github 저장할 폴더 경로 설정
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))  # 현재 파일 경로 기준
DATA_DIR = os.path.join(REPO_ROOT, "..", "data")  # `data/` 폴더가 한 단계 위에 있어야 함
os.makedirs(DATA_DIR, exist_ok=True)  # ✅ 폴더가 없으면 생성
print(f"📂 데이터 폴더 경로: {DATA_DIR}")

# 4.2. 로컬 저장할 폴더 경로 설정
#DATA_DIR = r"C:\Users\John\Downloads"
#os.makedirs(DATA_DIR, exist_ok=True)
#print(f"📂 데이터 폴더 경로: {DATA_DIR}")

# 4.3. API 요청 함수
def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get("response", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API 요청 실패: {e}")
        return []

# 5. JSON 저장 함수
def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

        
# 6. 경기 시작 시간 변환 및 저장
def save_match_start_time(match_id, start_time):
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


# 7. 경기전 배당률 JSON 저장 함수
def save_odds_json(match_id, odds_data):
    file_name = f"bet_{match_id}.json"
    file_path = os.path.join(DATA_DIR, file_name)

    if odds_data:
        save_json(file_path, odds_data)
        print(f"✅ 경기 전 배당률 데이터 저장 완료: {file_path}")
    else:
        print("⚠️ 경기 전 배당률 데이터가 없습니다. 빈 JSON 파일을 생성합니다.")
        save_json(file_path, [{"배팅사": "N/A", "배당률": "경기 전 데이터 없음"}])  # 빈 JSON 생성

# 8. 경기전 배당률 데이터 변환 함수
def process_odds_data(odds_details):
    if not odds_details:
        return [{"배팅사": "N/A", "배당률": "경기 전 데이터 없음"}]

    odds_data = []
    for bookmaker in odds_details:
        if "bookmakers" not in bookmaker:
            continue  # `bookmakers` 키가 없으면 패스

        bookmaker_name = bookmaker.get("name", "N/A")
        bets = bookmaker.get("bets", [])

        bet_list = []
        for bet in bets:
            bet_name = bet.get("name", "N/A")
            values = bet.get("values", [])

            for odd in values:
                bet_list.append({
                    "종류": bet_name,
                    "배당": odd.get("value", "N/A")
                })

        odds_data.append({"배팅사": bookmaker_name, "배당률": bet_list})

    return odds_data if odds_data else [{"배팅사": "N/A", "배당률": "경기 전 데이터 없음"}]

# 9. 경기 전 데이터 저장 함수
def save_json_with_match_id(match_id, data):
    file_name = f"real_live_{match_id}.json"
    file_path = os.path.join(DATA_DIR, file_name)
    save_json(file_path, data)
    print(f"✅ 경기전 데이터 저장 완료: {file_path}")

# 10. 경기 전 데이터 가져오기
def get_match_data(match_id):
    print(f"🔍 경기 데이터 수집 시작: Match ID = {match_id}")

    # 📌 10.1. API 엔드포인트 설정
    detail_url = f"https://v3.football.api-sports.io/fixtures?id={match_id}"
    odds_url = f"https://v3.football.api-sports.io/odds?fixture={match_id}"  # 경기 전 배당률 데이터 요청

    # 📌 10.2. API 데이터 요청
    match_details = fetch_data(detail_url)
    odds_details = fetch_data(odds_url)  # 배당률 데이터 가져오기

    if not match_details:
        print("⚠️ 경기 데이터를 찾을 수 없습니다.")
        return "NO_DATA"
    
    match_data = match_details[0]
    fixture_info = match_data.get("fixture", {})
    match_start_time = fixture_info.get("date", "UNKNOWN")
    teams = match_data.get("teams", {})
    events = match_data.get("events", [])
    stats = match_data.get("statistics", [])
    lineups = match_data.get("lineups", [])
    players = match_data.get("players", [])
    league_info = match_data.get("league", {})

    # 10.4. API 응답에서 경기 시작 시간 가져오기
    match_start_time = fixture_info.get("date", "UNKNOWN")
    print(f"⏳ API 응답에서 가져온 경기 시작 시간: {match_start_time}")
    
    # 10.5. start_time_kst를 match_start_time 그대로 사용
    match_start_time_kst = match_start_time if match_start_time != "UNKNOWN" else "UNKNOWN"
    
    # 10.6. 경기 시작 시간 JSON 저장 (UTC 및 KST 모두)
    save_match_start_time(match_id, match_start_time)

    # 10.7. 경기 상태 확인 및 저장 (🔹 추가된 부분)
    match_status = fixture_info.get("status", {}).get("long", "UNKNOWN")

    # 10.8 경기전 배당률 데이터 저장 (비어 있을 경우에도 저장)
    odds_data = process_odds_data(odds_details)
    save_odds_json(match_id, odds_data)

    # 10.9 경기 시작 시간 JSON 로드
    start_time_file = os.path.join(DATA_DIR, f"match_{match_id}_start.json")
    try:
        with open(start_time_file, "r", encoding="utf-8") as f:
            start_time_data = json.load(f)
            match_start_time_kst = start_time_data.get("start_time_kst", "UNKNOWN")
    except FileNotFoundError:
        match_start_time_kst = "UNKNOWN"
    

    # 10.10 경기 데이터 저장 (모든 필드 포함)
    match_json = {
        "경기 ID": match_id,
        "경기 날짜": match_start_time_kst,  # ✅ 수정된 부분
        "경기장": fixture_info.get("venue", {}).get("name", "N/A"),
        "도시": fixture_info.get("venue", {}).get("city", "N/A"),
        "경기 상태": match_status,
        "리그": league_info.get("name", "N/A"),
        "라운드": league_info.get("round", "N/A"),
        "심판": fixture_info.get("referee", "N/A"),
        "관중 수": fixture_info.get("attendance", "N/A"),
        "팀 정보": {
            "홈팀": {
                "이름": teams.get("home", {}).get("name", "N/A"),
                "로고": teams.get("home", {}).get("logo", "N/A")
            },
            "원정팀": {
                "이름": teams.get("away", {}).get("name", "N/A"),
                "로고": teams.get("away", {}).get("logo", "N/A")
            }
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
                "선발 선수": [player["player"]["name"] for player in lineup["startXI"]],
                "교체 선수": [player["player"]["name"] for player in lineup["substitutes"]]
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
        ],
    }
    
    # 10.11 경기 데이터 저장
    save_json_with_match_id(match_id, match_json)

    return "SAVED"

##############################################################


# 11. 특정 경기의 실시간 전체 배당률 가져오기
def fetch_live_odds(match_id):
    url = f"https://v3.football.api-sports.io/odds/live?fixture={match_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        odds_data = response.json()
        
        # ✅ 전체 API 응답 저장 (JSON 형식)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_file_name = f"raw_live_odds_{match_id}_{timestamp}.json"
        raw_file_path = os.path.join(DATA_DIR, raw_file_name)
        save_json(raw_file_path, odds_data)
        print(f"✅ API 전체 데이터 저장 완료: {raw_file_path}")
        
        return odds_data.get("response", [])
    except requests.exceptions.RequestException as e:
        print(f"⚠️ API 요청 실패: {e}")
        return []



# 12. 실시간 전체 배당률 저장
def save_live_odds(match_id):
    print(f"🔍 경기 ID {match_id} 실시간 전체 배당률 조회 중...")
    odds_data = fetch_live_odds(match_id)
    
    if not odds_data:
        print(f"⚠️ 실시간 배당률 데이터를 찾을 수 없습니다.")
        return
    
    # 12.1 원본 JSON 저장
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    raw_file_name = f"raw_live_odds_{match_id}_{timestamp}.json"
    raw_file_path = os.path.join(DATA_DIR, raw_file_name)
    save_json(raw_file_path, odds_data)
    print(f"✅ 원본 배당률 저장 완료: {raw_file_path}")

    # 12.2. 데이터 필터링 및 새로운 JSON 저장
    filter_live_odds(raw_file_path, match_id)
    

# 13. 필터링 함수 추가 (불필요한 데이터 제거)
def filter_live_odds(file_path, match_id):
    print(f"🔍 경기 ID {match_id} 배당률 데이터 필터링 중...")
    
    # 13.1 JSON 데이터 로드
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

        data = data.get("response", [])
        if not data:
            print("⚠️ 필터링할 배당률 데이터가 없습니다.")
            return
        data = data[0]
        
        
    # 13.2 필요한 데이터만 필터링
    filtered_data = {
        "fixture": {
            "id": data.get("fixture", {}).get("id", "N/A"),
            "status": data.get("fixture", {}).get("status", {})
        },
        "league": {
            "id": data.get("league", {}).get("id", "N/A"),
            "season": data.get("league", {}).get("season", "N/A")
        },
        "teams": {
            "home": {
                "id": data.get("teams", {}).get("home", {}).get("id", "N/A"),
                "name": data.get("teams", {}).get("home", {}).get("name", "N/A"),
                "goals": data.get("teams", {}).get("home", {}).get("goals", "N/A")
            },
            "away": {
                "id": data.get("teams", {}).get("away", {}).get("id", "N/A"),
                "name": data.get("teams", {}).get("away", {}).get("name", "N/A"),
                "goals": data.get("teams", {}).get("away", {}).get("goals", "N/A")
            }
        },
        "update": data.get("update", "N/A"),
        "odds": [
            {
                "name": bet.get("name", "N/A"),
                "values": bet.get("values", [])
            }
            for bookmaker in data.get("odds", []) for bet in bookmaker.get("bets", [])
            if bet.get("name") in ["Match Winner", "Over/Under 2.5", "Asian Handicap"]
        ]
    }

    # 13.3. 필터링된 JSON 저장
    filtered_file_name = f"filtered_live_odds_{match_id}.json"
    filtered_file_path = os.path.join(DATA_DIR, filtered_file_name)
    save_json(filtered_file_path, filtered_data)
    print(f"✅ 필터링된 배당률 저장 완료: {filtered_file_path}")

# 14. 실행
if __name__ == "__main__":
    
    match_id = 1208323  # 경기 ID 지정
    save_live_odds(match_id)
    result = get_match_data(match_id)
    
    print(f"🎯 실행 시작: Match ID = {match_id}")    
    print(f"✅ 실행 결과: {result}")
    print("🏁 END: 경기 데이터 수집 완료")       
    

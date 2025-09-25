import re
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

def extract_match_blob(html: str) -> dict:
    """Pull out matchCentreData JSON from WhoScored match page."""
    soup = BeautifulSoup(html, "lxml")
    script = None
    for s in soup.find_all("script"):
        if s.string and "matchCentreData" in s.string:
            script = s.string
            break
    if not script:
        raise ValueError("Could not find matchCentreData in page scripts")

    # Find assignment like: matchCentreData = {...};
    m = re.search(r"matchCentreData\s*=\s*(\{.*\});", script)
    if not m:
        raise ValueError("Could not extract matchCentreData assignment")
    blob = m.group(1)

    # Clean
    blob = blob.replace("undefined", "null")
    blob = re.sub(r",\s*([}\]])", r"\1", blob)

    return json.loads(blob)

def fetch_match(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = extract_match_blob(r.text)

    match_id = data.get("matchId")
    pid_name = data.get("playerIdNameDictionary", {})

    def side_block(side_key):
        side = data.get(side_key, {})
        return {
            "name": side.get("name"),
            "teamId": side.get("teamId"),
            "players": [
                {
                    "playerId": p.get("playerId"),
                    "name": p.get("name"),
                    "shirtNo": p.get("shirtNo"),
                    "position": p.get("position"),
                }
                for p in side.get("players", [])
            ],
            "formations": side.get("formations", []),
        }

    events = []
    for ev in data.get("events", []):
        e = {
            "id": ev.get("id"),
            "teamId": ev.get("teamId"),
            "playerId": ev.get("playerId"),
            "x": ev.get("x"),
            "y": ev.get("y"),
            "endX": ev.get("endX"),
            "endY": ev.get("endY"),
            "type": (ev.get("type") or {}).get("displayName"),
            "outcomeType": (ev.get("outcomeType") or {}).get("displayName"),
            "period": (ev.get("period") or {}).get("displayName"),
            "minute": ev.get("minute") or ev.get("expandedMinute"),
            "second": ev.get("second"),
            "isShot": bool(ev.get("isShot", False)),
            "isGoal": bool(ev.get("isGoal", False)),
            "expectedGoals": ev.get("expectedGoals"),
        }
        if e.get("playerId") and str(int(e["playerId"])) in pid_name:
            e["playerName"] = pid_name[str(int(e["playerId"]))]
        events.append(e)

    return {
        "matchId": match_id,
        "home": side_block("home"),
        "away": side_block("away"),
        "events": events,
    }

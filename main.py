import re
import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

def _extract_match_blob(html: str) -> dict:
    """
    WhoScored match pages embed a big JSON-ish object in a <script> near the top.
    We locate the <script> that contains 'matchId' and rebuild a dict.
    """
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")
    target = None
    for s in scripts:
        t = s.text or ""
        if "matchId" in t and "matchCentreData" in t or "formation" in t:
            target = t
            break
    if not target:
        # fallback: pick the first <script> containing matchId
        for s in scripts:
            t = s.text or ""
            if "matchId" in t:
                target = t
                break
    if not target:
        raise ValueError("Could not find embedded match data script.")

    # Minify
    code = re.sub(r"[\n\r\t]+", "", target)
    # Heuristic: extract the chunk starting at 'matchId' up to the last closing brace
    start = code.find("matchId")
    end = code.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("Unexpected script format.")
    chunk = code[start:end+1]

    # The original repo split on a long comma pattern; here we instead try to
    # locate a JSON object inside (starting from first '{' after 'matchId').
    first_brace = chunk.find("{")
    blob = chunk[first_brace:]
    # Now try to parse JSON by balancing braces. Sometimes it's JS, not pure JSON.
    # We attempt a few cleanups:
    blob = blob.replace("undefined", "null")
    # Remove trailing commas in objects/arrays (simple pass)
    blob = re.sub(r",\s*([}\]])", r"\1", blob)

    # The script is often already valid JSON
    try:
        data = json.loads(blob)
        return data
    except Exception:
        # Fallback: extract known keys using regex approach from your old main.py
        # Build a dict from key:value pairs like  key: {...} or key: [...]
        pairs = {}
        # split on ',            ' is brittle; use ',     "' occurrences as separators
        parts = re.split(r",\s{6,}", chunk)
        for part in parts:
            if ":" not in part: 
                continue
            k, v = part.split(":", 1)
            k = k.strip().strip("'\"")
            v = v.strip()
            try:
                pairs[k] = json.loads(v.replace("undefined", "null"))
            except Exception:
                pass
        if "matchCentreData" in pairs:
            return pairs["matchCentreData"]
        if "matchId" in pairs:
            return pairs
        raise

def _clean_events(raw_events, pid_name_dict):
    out = []
    for ev in raw_events:
        e = {}
        # basic
        e["id"] = ev.get("id")
        e["teamId"] = ev.get("teamId")
        e["playerId"] = ev.get("playerId")
        # coords (WhoScored 0..100)
        e["x"] = ev.get("x")
        e["y"] = ev.get("y")
        e["endX"] = ev.get("endX")
        e["endY"] = ev.get("endY")
        # labels
        e["type"] = (ev.get("type") or {}).get("displayName") or ev.get("type")
        e["outcomeType"] = (ev.get("outcomeType") or {}).get("displayName") or ev.get("outcomeType")
        e["period"] = (ev.get("period") or {}).get("displayName")
        e["minute"] = ev.get("minute") or ev.get("expandedMinute")
        e["second"] = ev.get("second")
        e["isShot"] = bool(ev.get("isShot", False))
        e["isGoal"] = bool(ev.get("isGoal", False))
        if "expectedGoals" in ev:
            e["expectedGoals"] = ev.get("expectedGoals")
        # convenience
        if e.get("playerId") and isinstance(e["playerId"], (int, float)):
            e["playerName"] = pid_name_dict.get(str(int(e["playerId"])))
        out.append(e)
    return out

def fetch_match(url: str) -> dict:
    """
    Returns a dict with keys:
    - matchId
    - home: { name, teamId, players:[{playerId, name, shirtNo, position}], formations:[{playerIds, formationName}] }
    - away: { ... }
    - events: [ cleaned events with type/outcome/x/y/endX/endY/isShot/isGoal/expectedGoals ]
    """
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = _extract_match_blob(r.text)

    # The blob already resembles your old match_data; normalize minimal fields
    match_id = data.get("matchId") or data.get("id")

    # playerIdNameDictionary often present
    pid_name = data.get("playerIdNameDictionary", {})
    # Build home/away shells
    def side_block(side_key):
        side = data.get(side_key, {})
        players = []
        for p in side.get("players", []):
            players.append({
                "playerId": p.get("playerId"),
                "name": p.get("name"),
                "shirtNo": p.get("shirtNo"),
                "position": p.get("position")
            })
        formations = side.get("formations", [])
        return {
            "name": side.get("name"),
            "teamId": side.get("teamId"),
            "players": players,
            "formations": formations
        }

    home = side_block("home")
    away = side_block("away")

    # Events
    raw_events = data.get("events") or data.get("matchCentreEventJson") or []
    events = _clean_events(raw_events, pid_name)

    return {
        "matchId": match_id,
        "home": home,
        "away": away,
        "events": events
    }

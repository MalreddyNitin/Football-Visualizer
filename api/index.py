import json
import re
from flask import Flask, request, jsonify
from main import fetch_match

app = Flask(__name__)

def team_side(md, name):
    if md["home"]["name"] == name:
        return "home"
    if md["away"]["name"] == name:
        return "away"
    return None

def lineup_players(md, side):
    # first formation first 11
    try:
        f = md[side]["formations"][0]
        pids = set(f["playerIds"][:11])
    except Exception:
        pids = set()
    res = []
    for p in md[side]["players"]:
        if not pids or p["playerId"] in pids:
            res.append({
                "playerId": p["playerId"],
                "name": p["name"],
                "shirtNo": p.get("shirtNo"),
                "position": p.get("position")
            })
    return res

def passes_for_team(md, events, team_id):
    """Return list of successful passes for team (order-preserving)."""
    out = []
    prev = None
    for ev in events:
        if ev.get("teamId") != team_id:
            prev = None
            continue
        if ev.get("type") == "Pass" and ev.get("outcomeType") == "Successful":
            out.append(ev)
            prev = ev
        else:
            prev = ev
    return out

def avg_positions_for_team(events, team_id):
    sums = {}   # {playerId: [sx, sy, n]}
    for ev in events:
        if ev.get("teamId") != team_id:
            continue
        pid = ev.get("playerId")
        if pid is None:
            continue
        # use start location
        x, y = ev.get("x"), ev.get("y")
        if x is None or y is None:
            continue
        s = sums.get(pid, [0.0, 0.0, 0])
        s[0] += float(x)
        s[1] += float(y)
        s[2] += 1
        sums[pid] = s
    avgs = {pid: {"x": sx/n, "y": sy/n, "count": n} for pid, (sx, sy, n) in sums.items() if n > 0}
    return avgs

def build_pass_network(md, events, team_name):
    side = team_side(md, team_name)
    if not side:
        raise ValueError(f"Team '{team_name}' not in this match.")
    team_id = md[side]["teamId"]
    # node meta
    roster = {p["playerId"]: p for p in md[side]["players"]}
    avgs = avg_positions_for_team(events, team_id)
    nodes = []
    for pid, pos in avgs.items():
        p = roster.get(pid, {"name": str(pid)})
        nodes.append({
            "playerId": pid,
            "name": p.get("name", str(pid)),
            "shirtNo": p.get("shirtNo"),
            "x": float(pos["x"]),
            "y": float(pos["y"])
        })
    # edges = consecutive passes between same-team players
    links = []
    # create quick map of index->playerId for pass sequence
    team_passes = [ev for ev in events if ev.get("teamId") == team_id and ev.get("type") == "Pass" and ev.get("outcomeType") == "Successful"]
    from collections import defaultdict
    pair_counts = defaultdict(int)
    for i in range(len(team_passes)-1):
        a = team_passes[i]
        b = team_passes[i+1]
        if a.get("playerId") and b.get("playerId") and a["playerId"] != b["playerId"]:
            pair_counts[(a["playerId"], b["playerId"])] += 1
    for (s, t), cnt in pair_counts.items():
        links.append({"source": s, "target": t, "count": cnt})
    return {"nodes": nodes, "links": links}

def box_passes(md, events, team_name):
    side = team_side(md, team_name)
    if not side:
        raise ValueError(f"Team '{team_name}' not in this match.")
    team_id = md[side]["teamId"]

    def in_box(x, y):
        # Using 100x100 WS space; scale to UEFA-ish: here assume box ~ x >= 85 and 18<=y<=82
        return x >= 85 and 18 <= y <= 82

    out = []
    for ev in events:
        if ev.get("teamId") != team_id: 
            continue
        if ev.get("type") != "Pass" or ev.get("outcomeType") != "Successful":
            continue
        x, y = float(ev.get("x", 0)), float(ev.get("y", 0))
        ex, ey = float(ev.get("endX", 0)), float(ev.get("endY", 0))
        if in_box(ex, ey) and not in_box(x, y):
            out.append({"x": x, "y": y, "endX": ex, "endY": ey})
    return {"passes": out}

def shots_split(md, events, team_name):
    side = team_side(md, team_name)
    if not side:
        raise ValueError(f"Team '{team_name}' not in this match.")
    team_id = md[side]["teamId"]
    shots, goals = [], []
    for ev in events:
        if ev.get("teamId") != team_id:
            continue
        if ev.get("isShot") or ev.get("type") in ("Shot", "Miss", "Goal"):
            x, y = float(ev.get("x", 0)), float(ev.get("y", 0))
            xg = None
            try:
                xg = float(ev.get("expectedGoals")) if ev.get("expectedGoals") is not None else None
            except Exception:
                xg = None
            rec = {"x": x, "y": y, "xG": xg}
            if ev.get("isGoal") or ev.get("type") == "Goal":
                goals.append(rec)
            else:
                shots.append(rec)
    return {"shots": shots, "goals": goals}

@app.get("/api/match")
def api_match():
    url = request.args.get("url", "")
    if not url:
        return ("Missing ?url=", 400)
    md = fetch_match(url)
    return jsonify({
        "matchId": md["matchId"],
        "home": md["home"]["name"],
        "away": md["away"]["name"]
    })

@app.get("/api/players")
def api_players():
    url = request.args.get("url", "")
    team = request.args.get("team", "")
    if not url or not team:
        return ("Missing ?url=&team=", 400)
    md = fetch_match(url)
    side = team_side(md, team)
    if not side:
        return (f"Team '{team}' not in this match.", 400)
    return jsonify(lineup_players(md, side))

@app.get("/api/pass-network")
def api_pass_network():
    url = request.args.get("url", "")
    team = request.args.get("team", "")
    if not url or not team:
        return ("Missing ?url=&team=", 400)
    md = fetch_match(url)
    data = build_pass_network(md, md["events"], team)
    return jsonify(data)

@app.get("/api/box-passes")
def api_box_passes():
    url = request.args.get("url", "")
    team = request.args.get("team", "")
    if not url or not team:
        return ("Missing ?url=&team=", 400)
    md = fetch_match(url)
    return jsonify(box_passes(md, md["events"], team))

@app.get("/api/shots")
def api_shots():
    url = request.args.get("url", "")
    team = request.args.get("team", "")
    if not url or not team:
        return ("Missing ?url=&team=", 400)
    md = fetch_match(url)
    return jsonify(shots_split(md, md["events"], team))

# Important: Vercel detects the Flask `app` variable as the handler.

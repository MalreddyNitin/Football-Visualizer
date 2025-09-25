# api/index.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import pandas as pd

from .core import fetch_match_html, parse_match_json, create_events_df, sides_and_ids
from .compute import (
    pass_network,
    box_passes,
    shots_data,
    team_meta,
    team_players,
)

app = FastAPI(title="Football Visualizer API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lock this to your domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/match")
def api_match(url: str = Query(..., description="WhoScored match center URL")):
    html = fetch_match_html(url)
    match = parse_match_json(html)
    return {
        "matchId": match["matchId"],
        "home": match["home"]["name"],
        "away": match["away"]["name"],
        "region": match.get("region"),
        "league": match.get("league"),
        "season": match.get("season"),
        "competitionType": match.get("competitionType"),
        "competitionStage": match.get("competitionStage"),
    }


@app.get("/api/players")
def api_players(url: str, team: Optional[str] = None, side: Optional[str] = None):
    """
    Provide either ?team=Team Name OR ?side=home/away
    """
    html = fetch_match_html(url)
    match = parse_match_json(html)

    if team:
        players = team_players(match, team)
    else:
        if side not in ("home", "away"):
            return {"error": "Provide ?team=Team Name or ?side=home|away"}
        players = [{"playerId": p["playerId"], "name": p["name"], "position": p.get("position"), "shirtNo": p.get("shirtNo")}
                   for p in match[side]["players"]]
    return {"players": players}


@app.get("/api/pass-network")
def api_pass_network(url: str, team: str):
    html = fetch_match_html(url)
    match = parse_match_json(html)
    events_df = create_events_df(match)
    data = pass_network(events_df, match, team)
    return data


@app.get("/api/box-passes")
def api_box_passes(url: str, team: str):
    html = fetch_match_html(url)
    match = parse_match_json(html)
    events_df = create_events_df(match)
    tid, _ = team_meta(match, team)
    data = box_passes(events_df, tid)
    return {"passes": data}


@app.get("/api/shots")
def api_shots(url: str, team: str):
    html = fetch_match_html(url)
    match = parse_match_json(html)
    events_df = create_events_df(match)
    tid, _ = team_meta(match, team)
    data = shots_data(events_df, tid)
    return data

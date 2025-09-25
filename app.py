from fastapi import FastAPI
from fastapi.responses import JSONResponse
import io, base64
import matplotlib.pyplot as plt

from main import getMatchData, createEventsDF
import visuals

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "msg": "Football Analytics API running 🚀"}

@app.get("/match")
def match(url: str):
    """Return raw match JSON."""
    data = getMatchData(url)
    return JSONResponse(content=data)

@app.get("/players")
def players(url: str):
    """Return all player names from a match for dropdowns."""
    data = getMatchData(url)

    home_players = [p["name"] for p in data["home"]["players"]]
    away_players = [p["name"] for p in data["away"]["players"]]

    return {
        "homeTeam": data["home"]["name"],
        "awayTeam": data["away"]["name"],
        "homePlayers": home_players,
        "awayPlayers": away_players
    }

@app.get("/heatmap")
def heatmap(url: str, player: str):
    """Return base64 heatmap image for given player."""
    data = getMatchData(url)
    events_df = createEventsDF(data)

    fig, ax = plt.subplots(figsize=(10,7))
    visuals.plotHeatmap(events_df, player, fig, ax)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")

    return {"player": player, "heatmap": img}

@app.get("/passnetwork")
def passnetwork(url: str, team: str):
    """Return base64 pass network image for given team."""
    data = getMatchData(url)
    events_df = createEventsDF(data)

    fig, ax = plt.subplots(figsize=(12,9))
    visuals.createPassNetworks(
        match_data=data,
        events_df=events_df,
        matchId=data["matchId"],
        team=team,
        ax=ax,
        max_line_width=6,
        marker_size=1200,
        edgewidth=2,
        dh_arrow_width=20,
        marker_color='#0e5cba',
        marker_edge_color='w',
        shrink=20,
        kit_no_size=20
    )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")

    return {"team": team, "passnetwork": img}

@app.get("/shotmap")
def shotmap(url: str, team: str):
    """Return base64 shot map image for given team."""
    data = getMatchData(url)
    events_df = createEventsDF(data)

    fig, ax = plt.subplots(figsize=(12,9))
    visuals.createShotmap(
        match_data=data,
        events_df=events_df,
        team=team,
        pitchcolor="black",
        shotcolor="white",
        goalcolor="red",
        titlecolor="white",
        legendcolor="white",
        marker_size=300,
        fig=fig,
        ax=ax
    )

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")

    return {"team": team, "shotmap": img}

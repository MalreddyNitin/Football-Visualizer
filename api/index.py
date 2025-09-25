from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/match")
async def match(url: str = Query(...)):
    # For now return fake data
    return {"home": "Bayern Munich", "away": "Inter"}

@app.get("/api/pass-network")
async def pass_network(url: str, team: str):
    nodes = [
        {"playerId": 1, "name": "Player A", "shirtNo": 7, "x": 30, "y": 40},
        {"playerId": 2, "name": "Player B", "shirtNo": 10, "x": 60, "y": 50},
    ]
    links = [
        {"source": 1, "target": 2, "count": 12},
        {"source": 2, "target": 1, "count": 7},
    ]
    return {"nodes": nodes, "links": links}

@app.get("/api/box-passes")
async def box_passes(url: str, team: str):
    passes = [
        {"x": 80, "y": 40, "endX": 100, "endY": 45},
        {"x": 85, "y": 50, "endX": 102, "endY": 38},
    ]
    return {"passes": passes}

@app.get("/api/shots")
async def shots(url: str, team: str):
    shots = [
        {"x": 70, "y": 40, "xG": 0.1},
        {"x": 90, "y": 55, "xG": 0.3},
    ]
    goals = [
        {"x": 95, "y": 45, "xG": 0.4},
    ]
    return {"shots": shots, "goals": goals}

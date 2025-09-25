# api/compute.py
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

def team_meta(match_data: Dict[str, Any], team_name: str) -> Tuple[int, str]:
    if match_data["home"]["name"] == team_name:
        return match_data["home"]["teamId"], "home"
    return match_data["away"]["teamId"], "away"


def players_list(match_data: Dict[str, Any], side: str) -> List[Dict[str, Any]]:
    assert side in ("home", "away")
    out = []
    for p in match_data[side]["players"]:
        out.append(
            {
                "playerId": p["playerId"],
                "name": p["name"],
                "position": p.get("position"),
                "shirtNo": p.get("shirtNo"),
            }
        )
    return out


def pass_network(events_df: pd.DataFrame, match_data: Dict[str, Any], team_name: str) -> Dict[str, Any]:
    team_id, side = team_meta(match_data, team_name)

    # build mapper for playerId-> (name, shirtNo)
    id2meta = {}
    for p in match_data[side]["players"]:
        id2meta[p["playerId"]] = {"name": p["name"], "shirtNo": p.get("shirtNo")}

    df = events_df.copy()
    df = df[df["teamId"] == team_id]
    df = df[df["type"] == "Pass"].copy()
    # outcomeType may be NaN for some events; keep both, frontend can filter
    df["playerId"] = pd.to_numeric(df["playerId"], errors="coerce").dropna().astype(int)

    # Define recipient as "next event by same team"
    df["passRecipientId"] = df["playerId"].shift(-1)
    df["passRecipientId"] = pd.to_numeric(df["passRecipientId"], errors="coerce")

    df = df.dropna(subset=["passRecipientId"])
    df["passRecipientId"] = df["passRecipientId"].astype(int)

    # Remove self-passes
    df = df[df["playerId"] != df["passRecipientId"]].copy()

    # Average locations for each player (simple average of start locations)
    locs = (
        df.groupby("playerId")[["x", "y"]]
        .mean()
        .rename(columns={"x": "avgX", "y": "avgY"})
        .reset_index()
    )

    # Count edges + (optional) simple weight = count
    edges = (
        df.groupby(["playerId", "passRecipientId"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    # nodes with metadata
    nodes = []
    for _, row in locs.iterrows():
        pid = int(row["playerId"])
        meta = id2meta.get(pid, {})
        nodes.append(
            {
                "playerId": pid,
                "name": meta.get("name", str(pid)),
                "shirtNo": meta.get("shirtNo"),
                "x": float(row["avgX"]),
                "y": float(row["avgY"]),
            }
        )

    links = []
    for _, r in edges.iterrows():
        src = int(r["playerId"])
        dst = int(r["passRecipientId"])
        links.append({"source": src, "target": dst, "count": int(r["count"])})

    return {"nodes": nodes, "links": links}


def box_passes(events_df: pd.DataFrame, team_id: int) -> List[Dict[str, float]]:
    """
    Return list of successful passes that END in the penalty box.
    Coordinates are kept in WhoScored units [0..100] so frontend can decide scaling.
    """
    df = events_df.copy()
    df = df[(df["teamId"] == team_id) & (df["type"] == "Pass")].copy()
    df = df[df["outcomeType"] == "Successful"]

    # 120x80 SB → WhoScored is 100x100; we keep the original WS scale, but box check mirrors statsbomb dimensions:
    # In WS scale, a common approximation for penalty box: x_end >= 85 (of 100), y in [18, 82] (scaled from 80)
    # We'll be more strict and use ~ 85 for x.
    def in_box(xend, yend):
        return (xend >= 85) and (18 <= yend <= 82)

    mask = df.apply(lambda r: in_box(r["endX"], r["endY"]), axis=1)
    df = df[mask]

    return [
        {"x": float(r.x), "y": float(r.y), "endX": float(r.endX), "endY": float(r.endY)}
        for _, r in df.iterrows()
    ]


def shots_data(events_df: pd.DataFrame, team_id: int) -> Dict[str, Any]:
    df = events_df.copy()
    df = df[(df["teamId"] == team_id) & (df["isOwnGoal"] == False)].copy() if "isOwnGoal" in df.columns else df[df["teamId"] == team_id]

    goals = df[df["type"] == "Goal"].copy()
    shots = df[(df["isShot"] == True) & (df["type"] != "Goal")].copy()

    def to_pt(r):
        # keep WS scale [0..100]; frontend can flip if needed
        return {"x": float(r["x"]), "y": float(r["y"]), "xG": float(r.get("expectedGoals", 0.0) or 0.0)}

    return {
        "goals": [to_pt(r) for _, r in goals.iterrows()],
        "shots": [to_pt(r) for _, r in shots.iterrows()],
    }


def team_players(match_data: Dict[str, Any], team_name: str) -> List[Dict[str, Any]]:
    tid, side = team_meta(match_data, team_name)
    return players_list(match_data, side)

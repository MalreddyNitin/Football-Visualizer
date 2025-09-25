# api/core.py
import re
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_match_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse_match_json(html: str) -> Dict[str, Any]:
    """
    On WhoScored match pages, the first <script> inside #layout-wrapper
    contains a big JS object with matchId, home, away, events, etc.
    We extract its JSON blobs like your original Selenium approach did.
    """
    soup = BeautifulSoup(html, "lxml")
    layout = soup.select_one("#layout-wrapper")
    if not layout:
        raise ValueError("Could not find #layout-wrapper in page.")

    # The first script tag under layout-wrapper
    script = layout.find("script")
    if not script or not script.text:
        raise ValueError("Could not find embedded match JSON script.")

    script_content = re.sub(r"[\n\t]+", "", script.text)
    # restrict to the object section
    if "matchId" not in script_content:
        raise ValueError("Embedded JSON not found (no 'matchId').")
    script_content = script_content[script_content.index("matchId") : script_content.rindex("}")]

    parts = list(filter(None, script_content.strip().split(",            ")))
    metadata = parts.pop(1)  # the large JSON chunk

    match_data = json.loads(metadata[metadata.index("{") :])
    keys = [item[: item.index(":")].strip() for item in parts]
    vals = [item[item.index(":") + 1 :].strip() for item in parts]

    for k, v in zip(keys, vals):
        match_data[k] = json.loads(v)

    # add breadcrumb info (region/league/season) from page header
    breadcrumb = soup.select_one("#breadcrumb-nav")
    if breadcrumb:
        region = breadcrumb.select_one("span")
        link = breadcrumb.select_one("a")
        region_txt = region.get_text(strip=True) if region else ""
        league_season_txt = link.get_text(strip=True) if link else ""
        pieces = league_season_txt.split(" - ")
        league = pieces[0] if pieces else ""
        season = pieces[1] if len(pieces) > 1 else ""
        if len(pieces) == 2:
            competition_type = "League"
            competition_stage = ""
        elif len(pieces) == 3:
            competition_type = "Knock Out"
            competition_stage = pieces[-1]
        else:
            competition_type = ""
            competition_stage = ""

        match_data["region"] = region_txt
        match_data["league"] = league
        match_data["season"] = season
        match_data["competitionType"] = competition_type
        match_data["competitionStage"] = competition_stage

    return match_data


def create_events_df(match_data: Dict[str, Any]) -> pd.DataFrame:
    """Vectorized, headless version of your createEventsDF."""
    events = match_data["events"]
    base_cols = {
        "matchId": match_data["matchId"],
        "startDate": match_data.get("startDate"),
        "startTime": match_data.get("startTime"),
        "score": match_data.get("score"),
        "ftScore": match_data.get("ftScore"),
        "htScore": match_data.get("htScore"),
        "etScore": match_data.get("etScore"),
        "venueName": match_data.get("venueName"),
        "maxMinute": match_data.get("maxMinute"),
    }
    # attach common cols to each event dict
    for ev in events:
        ev.update(base_cols)

    df = pd.DataFrame(events)
    # period/type/outcome -> displayName
    df["events_id"] = df["id"]
    df["period"] = pd.json_normalize(df["period"])["displayName"]
    df["type"] = pd.json_normalize(df["type"])["displayName"]
    df["outcomeType"] = pd.json_normalize(df["outcomeType"])["displayName"]

    # cardType displayName if exists
    try:
        x = df["cardType"].fillna({i: {} for i in df.index})
        df["cardType"] = pd.json_normalize(x)["displayName"].fillna(False)
    except KeyError:
        df["cardType"] = False

    # satisfiedEventsTypes -> numeric codes using dictionary
    typeDict = match_data["matchCentreEventTypeJson"]
    def convert_satisfied(row):
        return [list(typeDict.keys())[list(typeDict.values()).index(e)] for e in row]
    df["satisfiedEventsTypes"] = df["satisfiedEventsTypes"].apply(convert_satisfied)

    # qualifiers -> substitute type with displayName (when present)
    def normalize_qualifiers(qs):
        if not qs:
            return []
        out = []
        for q in qs:
            qq = dict(q)
            t = qq.get("type")
            if isinstance(t, dict) and "displayName" in t:
                qq["type"] = t["displayName"]
            out.append(qq)
        return out
    df["qualifiers"] = df["qualifiers"].apply(normalize_qualifiers)

    # isShot / isGoal default False
    if "isShot" in df.columns:
        df["isShot"] = df["isShot"].replace(np.nan, False)
    else:
        df["isShot"] = False
    if "isGoal" in df.columns:
        df["isGoal"] = df["isGoal"].replace(np.nan, False)
    else:
        df["isGoal"] = False

    # playerName from map
    df.loc[df.playerId.notna(), "playerId"] = df.loc[df.playerId.notna(), "playerId"].astype(int).astype(str)
    name_map = match_data.get("playerIdNameDictionary", {})
    df.insert(df.columns.get_loc("playerId") + 1, "playerName", df["playerId"].map(name_map))

    # home/away tag
    h_id = match_data["home"]["teamId"]
    a_id = match_data["away"]["teamId"]
    df.insert(df.columns.get_loc("teamId") + 1, "h_a", df["teamId"].map({h_id: "h", a_id: "a"}))

    # Add simple shot body part & situation from qualifiers
    df["shotBodyType"] = np.nan
    df["situation"] = np.nan

    def body_from_quals(quals):
        for q in quals:
            t = q.get("type")
            if t in ("RightFoot", "LeftFoot", "Head", "OtherBodyPart"):
                return t
        return np.nan

    def situation_from_quals(quals):
        out = None
        for q in quals:
            t = q.get("type")
            if t in ("FromCorner", "SetPiece", "DirectFreekick"):
                out = t
            if t == "RegularPlay":
                out = "OpenPlay"
        return out

    shot_mask = df["isShot"] == True
    df.loc[shot_mask, "shotBodyType"] = df.loc[shot_mask, "qualifiers"].apply(body_from_quals)
    df.loc[shot_mask, "situation"] = df.loc[shot_mask, "qualifiers"].apply(situation_from_quals)

    return df


def sides_and_ids(match_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return match_data["home"], match_data["away"]

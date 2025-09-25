# main.py
import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
import numpy as np
from collections import OrderedDict

# ----------------------------
# Whoscored main entry
# ----------------------------
MAIN_URL = "https://1xbet.whoscored.com/"

def getMatchData(url: str):
    """
    Fetch match JSON data directly from the <script> tag on WhoScored match page.
    No Selenium/Playwright needed.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/120.0 Safari/537.36"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # Match JSON is embedded in a <script> tag
    script_tag = soup.find("script", string=re.compile("matchId"))
    if not script_tag:
        raise ValueError("❌ Could not find match JSON script on page")

    script_content = script_tag.string
    script_content = re.sub(r"[\n\t]*", "", script_content)
    script_content = script_content[script_content.index("matchId"):script_content.rindex("}")]

    script_content_list = list(filter(None, script_content.strip().split(',            ')))
    metadata = script_content_list.pop(1)

    match_data = json.loads(metadata[metadata.index('{'):])
    keys = [item[:item.index(':')].strip() for item in script_content_list]
    values = [item[item.index(':') + 1:].strip() for item in script_content_list]
    for key, val in zip(keys, values):
        match_data[key] = json.loads(val)

    # Region, league, season
    breadcrumb = soup.select_one("#breadcrumb-nav")
    if breadcrumb:
        parts = breadcrumb.get_text(" ", strip=True).split(" - ")
        region = parts[0]
        league = parts[1] if len(parts) > 1 else ""
        season = parts[2] if len(parts) > 2 else ""
    else:
        region, league, season = "", "", ""

    match_data["region"] = region
    match_data["league"] = league
    match_data["season"] = season

    return match_data


def createEventsDF(data):
    """Convert match_data['events'] into a clean DataFrame"""
    events = data["events"]
    df = pd.DataFrame(events)

    # Clean type/outcome/period
    if "type" in df.columns:
        df["type"] = pd.json_normalize(df["type"])["displayName"]
    if "outcomeType" in df.columns:
        df["outcomeType"] = pd.json_normalize(df["outcomeType"])["displayName"]
    if "period" in df.columns:
        df["period"] = pd.json_normalize(df["period"])["displayName"]

    # Add player names
    if "playerId" in df.columns:
        df.loc[df.playerId.notna(), "playerId"] = df.loc[df.playerId.notna(), "playerId"].astype(int).astype(str)
        df.insert(
            loc=df.columns.get_loc("playerId") + 1,
            column="playerName",
            value=df["playerId"].map(data["playerIdNameDictionary"])
        )

    return df


def createMatchesDF(data):
    """Basic matches DataFrame"""
    cols = ["matchId", "attendance", "venueName", "startTime", "startDate", "score", "home", "away", "referee"]
    matches_df = pd.DataFrame([{k: v for k, v in data.items() if k in cols}])
    return matches_df.set_index("matchId")


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    url = "https://1xbet.whoscored.com/Matches/404786/Live/Europe-Champions-League-2009-2010-Bayern-Munich-Inter"
    match_data = getMatchData(url)
    print("✅ Match ID:", match_data["matchId"])
    events_df = createEventsDF(match_data)
    print("Events shape:", events_df.shape)

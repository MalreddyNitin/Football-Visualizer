import json
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# === Headless browser context ===
def get_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # accept cookies if popup appears
        try:
            page.locator("//button[contains(text(), 'Accept all')]").click(timeout=5000)
        except:
            pass

        html = page.content()
        browser.close()
        return html


# === Scrape match data ===
def getMatchData(url: str):
    html = get_html(url)
    soup = BeautifulSoup(html, "lxml")

    # Extract JSON from <script>
    script_tag = soup.find("script", text=re.compile("matchId"))
    script_content = script_tag.string

    script_content = re.sub(r"[\n\t]*", "", script_content)
    script_content = script_content[script_content.index("matchId"):script_content.rindex("}")]
    script_content_list = list(filter(None, script_content.strip().split(",            ")))
    metadata = script_content_list.pop(1)

    match_data = json.loads(metadata[metadata.index("{"):])
    keys = [item[:item.index(":")].strip() for item in script_content_list]
    values = [item[item.index(":") + 1:].strip() for item in script_content_list]
    for key, val in zip(keys, values):
        match_data[key] = json.loads(val)

    # basic info
    breadcrumb = soup.select_one("#breadcrumb-nav a").get_text(strip=True)
    parts = breadcrumb.split(" - ")
    match_data["league"] = parts[0]
    match_data["season"] = parts[1] if len(parts) > 1 else ""
    return match_data


# === Convert match data to pandas DF ===
def createEventsDF(data):
    events = data["events"]
    df = pd.DataFrame(events)

    # add player names
    df.loc[df.playerId.notna(), "playerId"] = (
        df.loc[df.playerId.notna(), "playerId"].astype(int).astype(str)
    )
    df.insert(
        loc=df.columns.get_loc("playerId") + 1,
        column="playerName",
        value=df["playerId"].map(data["playerIdNameDictionary"]),
    )

    # normalize some nested fields
    df["period"] = pd.json_normalize(df["period"])["displayName"]
    df["type"] = pd.json_normalize(df["type"])["displayName"]
    df["outcomeType"] = pd.json_normalize(df["outcomeType"])["displayName"]
    if "isShot" not in df:
        df["isShot"] = False
    if "isGoal" not in df:
        df["isGoal"] = False
    return df


def createMatchesDF(data):
    cols = ["matchId", "venueName", "startTime", "startDate", "score", "home", "away"]
    df = pd.DataFrame([{k: v for k, v in data.items() if k in cols}])
    return df.set_index("matchId")


def getHomeid(data):
    return data["home"]["teamId"]

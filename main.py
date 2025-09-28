import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# Utility: Extract embedded match JSON from WhoScored HTML
# -------------------------------------------------------------------
def _extract_match_blob(html: str) -> dict:
    """
    WhoScored match pages embed a big JSON-ish object in a <script>.
    We locate the <script> that contains 'matchId' and parse it.
    """
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")

    target = None
    for s in scripts:
        t = s.text or ""
        if "matchId" in t and "matchCentreData" in t:
            target = t
            break

    if not target:
        raise ValueError("Could not find embedded match JSON in page")

    # Extract JSON-ish string
    match = re.search(r"matchCentreData\s*=\s*({.*});", target)
    if not match:
        raise ValueError("Could not parse matchCentreData block")

    data = json.loads(match.group(1))
    return data


# -------------------------------------------------------------------
# Public function: Download & parse WhoScored match
# -------------------------------------------------------------------
def getMatchData(url: str) -> dict:
    """
    Download match page and return parsed match JSON (match_data).
    """
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    return _extract_match_blob(resp.text)


# -------------------------------------------------------------------
# Convert match JSON into DataFrames
# -------------------------------------------------------------------
def createEventsDF(match_data: dict) -> pd.DataFrame:
    """
    Turn the 'events' list into a Pandas DataFrame.
    """
    events = match_data.get("events", [])
    return pd.DataFrame(events)


def createMatchesDF(match_data: dict) -> pd.DataFrame:
    """
    Turn top-level match info into a one-row DataFrame.
    Useful if you want to store/compare multiple matches.
    """
    meta = {
        "matchId": match_data.get("matchId"),
        "homeTeam": match_data.get("home", {}).get("name"),
        "awayTeam": match_data.get("away", {}).get("name"),
        "homeScore": match_data.get("home", {}).get("score"),
        "awayScore": match_data.get("away", {}).get("score"),
    }
    return pd.DataFrame([meta])


# -------------------------------------------------------------------
# Convenience if you want to test this file directly
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Example WhoScored match (replace with a real URL)
    url = "https://www.whoscored.com/Matches/1736362/Live/England-Premier-League-2023-2024-Arsenal-Manchester-City"
    match_data = getMatchData(url)

    print("Match ID:", match_data["matchId"])
    events_df = createEventsDF(match_data)
    matches_df = createMatchesDF(match_data)

    print("Events shape:", events_df.shape)
    print("Matches DF:")
    print(matches_df.head())

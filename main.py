import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# Headers (spoofing a real Chrome browser)
# -------------------------------------------------------------------
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://www.whoscored.com/",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "dnt": "1",
}

# -------------------------------------------------------------------
# Utility: Extract embedded match JSON
# -------------------------------------------------------------------
def _extract_match_blob(html: str) -> dict:
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

    match = re.search(r"matchCentreData\s*=\s*({.*});", target)
    if not match:
        raise ValueError("Could not parse matchCentreData block")

    return json.loads(match.group(1))

# -------------------------------------------------------------------
# Public function: Download & parse with cookie session
# -------------------------------------------------------------------
def getMatchData(url: str) -> dict:
    """
    Fetch WhoScored match JSON, handling both www.whoscored.com and 1xbet.whoscored.com domains.
    Uses a session to accept cookies first before requesting match data.
    """

    session = requests.Session()
    session.headers.update(HEADERS)

    # --- Step 1: Normalize URL to www.whoscored.com
    if "1xbet.whoscored.com" in url:
        url_www = url.replace("1xbet.whoscored.com", "www.whoscored.com")
    else:
        url_www = url

    # --- Step 2: Warm up cookies from www
    try:
        session.get("https://www.whoscored.com/", timeout=15)
        resp = session.get(url_www, timeout=15)

        if resp.status_code == 403:
            raise requests.HTTPError("403 Forbidden – likely cookie/session/IP issue")

        resp.raise_for_status()
        return _extract_match_blob(resp.text)

    except requests.HTTPError:
        # --- Step 3: If www fails, fall back to 1xbet mirror
        if "1xbet.whoscored.com" not in url:
            url_1xbet = url.replace("www.whoscored.com", "1xbet.whoscored.com")
        else:
            url_1xbet = url

        session.get("https://1xbet.whoscored.com/", timeout=15)
        resp = session.get(url_1xbet, timeout=15)

        if resp.status_code == 403:
            raise RuntimeError(
                "403 Forbidden even after cookie warm-up. "
                "This may be due to IP blocking (common on Render/Fly.io). "
                "Try running locally or via a proxy."
            )

        resp.raise_for_status()
        return _extract_match_blob(resp.text)

# -------------------------------------------------------------------
# DF creators
# -------------------------------------------------------------------
def createEventsDF(match_data: dict) -> pd.DataFrame:
    return pd.DataFrame(match_data.get("events", []))

def createMatchesDF(match_data: dict) -> pd.DataFrame:
    meta = {
        "matchId": match_data.get("matchId"),
        "homeTeam": match_data.get("home", {}).get("name"),
        "awayTeam": match_data.get("away", {}).get("name"),
        "homeScore": match_data.get("home", {}).get("score"),
        "awayScore": match_data.get("away", {}).get("score"),
    }
    return pd.DataFrame([meta])

# -------------------------------------------------------------------
# Debug
# -------------------------------------------------------------------
if __name__ == "__main__":
    test_url = "https://www.whoscored.com/Matches/1736362/Live/England-Premier-League-2023-2024-Arsenal-Manchester-City"
    match_data = getMatchData(test_url)
    print("Match ID:", match_data["matchId"])
    events_df = createEventsDF(match_data)
    print("Events:", events_df.shape)

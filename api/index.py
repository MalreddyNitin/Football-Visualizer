# api/index.py
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import main  # your lightweight scraper


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url = query.get("url", [None])[0]

        if not url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'url' query parameter")
            return

        try:
            match_data = main.getMatchData(url)
            events_df = main.createEventsDF(match_data)

            # List of unique player names for dropdown
            players = sorted(events_df["playerName"].dropna().unique().tolist())

            response = {
                "matchId": match_data.get("matchId"),
                "league": match_data.get("league"),
                "season": match_data.get("season"),
                "home": match_data.get("home", {}).get("name"),
                "away": match_data.get("away", {}).get("name"),
                "players": players,
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode("utf-8"))

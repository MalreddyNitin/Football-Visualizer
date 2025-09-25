import json
from urllib.parse import parse_qs
from api.main import fetch_match

def handler(request, response):
    try:
        query = parse_qs(request.query_string)
        url = query.get("url", [None])[0]
        team = query.get("team", [None])[0]
        path = request.path

        if not url:
            response.status_code = 400
            return response.send(json.dumps({"error": "Missing url"}))

        match = fetch_match(url)

        if path.endswith("/players"):
            if not team:
                raise ValueError("Need ?team=")
            side = match["home"] if match["home"]["name"] == team else match["away"]
            return response.send(json.dumps(side["players"]))

        if path.endswith("/pass-network"):
            events = [
                e for e in match["events"] if e["type"] == "Pass" and e["outcomeType"] == "Successful"
            ]
            return response.send(json.dumps({"passes": events}))

        if path.endswith("/shots"):
            shots = [e for e in match["events"] if e["isShot"]]
            goals = [e for e in shots if e["isGoal"]]
            return response.send(json.dumps({"shots": shots, "goals": goals}))

        return response.send(json.dumps({"matchId": match["matchId"]}))

    except Exception as e:
        response.status_code = 500
        return response.send(json.dumps({"error": str(e)}))

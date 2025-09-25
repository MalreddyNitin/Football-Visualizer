from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import io, base64
import matplotlib.pyplot as plt

from main import getMatchData, createEventsDF, getHomeid
import visuals

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "msg": "Football Analytics API running 🚀"}

@app.get("/match")
def match(url: str):
    data = getMatchData(url)
    return JSONResponse(content=data)

@app.get("/heatmap")
def heatmap(url: str, player: str):
    data = getMatchData(url)
    events_df = createEventsDF(data)
    fig, ax = plt.subplots(figsize=(10,7))
    visuals.plotHeatmap(events_df, player, fig, ax)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")
    return {"player": player, "heatmap": img}

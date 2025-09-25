# visuals.py (web-friendly)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
from matplotlib.patches import ConnectionPatch
from matplotlib.colors import to_rgba
from itertools import combinations
import seaborn as sns
from sklearn.cluster import KMeans

# ---------------------------
# Helper: Save fig to BytesIO
# ---------------------------
import io
def fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    return buf

# ---------------------------
# Example Shotmap
# ---------------------------
def create_shotmap(events_df, hometeam, awayteam, homeid, awayid,
                   pitchcolor="black", shotcolor="white", goalcolor="red",
                   marker_size=300):
    total_shots = events_df[events_df["isOwnGoal"] == False].copy()
    team_shots = total_shots[total_shots["teamId"] == homeid].copy()
    team_shots["x"] = 105 - team_shots["x"]
    team_shots["y"] = 68 - team_shots["y"]

    goals = team_shots[team_shots["eventType"] == "Goal"]
    shots = team_shots[team_shots["eventType"] != "Goal"]

    fig, ax = plt.subplots(figsize=(8, 6))
    pitch = Pitch(pitch_type="uefa", pitch_color=pitchcolor, line_color="white")
    pitch.draw(ax=ax)

    pitch.scatter(goals.x, goals.y, s=marker_size, c=goalcolor, edgecolors="black", ax=ax, label="Goal")
    pitch.scatter(shots.x, shots.y, s=marker_size, c=shotcolor, edgecolors="grey", ax=ax, label="Shot")

    ax.set_title(f"{hometeam} vs {awayteam} Shotmap", color="white")
    ax.legend(facecolor=pitchcolor)

    fig.patch.set_facecolor(pitchcolor)
    return fig_to_bytes(fig)

# ---------------------------
# Example Pass Network
# ---------------------------
def create_pass_network(events_df, match_data, team, max_line_width=6):
    # Pick team id
    if match_data["home"]["name"] == team:
        teamId = match_data["home"]["teamId"]
        venue = "home"
    else:
        teamId = match_data["away"]["teamId"]
        venue = "away"

    passes = events_df[(events_df["teamId"] == teamId) & (events_df["type"] == "Pass") & (events_df["outcomeType"] == "Successful")]

    avg_pos = passes.groupby("playerId")[["x", "y"]].mean()
    pass_counts = passes.groupby(["playerId", "passRecipientId"]).size().reset_index(name="count")

    fig, ax = plt.subplots(figsize=(8, 6))
    pitch = Pitch(pitch_type="opta", pitch_color="black", line_color="white")
    pitch.draw(ax=ax)

    # Draw player avg positions
    for pid, row in avg_pos.iterrows():
        pitch.scatter(row["x"], row["y"], s=400, color="blue", edgecolors="white", ax=ax)
        ax.text(row["x"], row["y"], str(pid), ha="center", va="center", color="white")

    # Draw passes
    for _, row in pass_counts.iterrows():
        if row["count"] >= 3:  # filter
            p1 = avg_pos.loc[row["playerId"]]
            p2 = avg_pos.loc[row["passRecipientId"]]
            con = ConnectionPatch([p2["x"], p2["y"]], [p1["x"], p1["y"]],
                                  coordsA="data", coordsB="data",
                                  arrowstyle="simple",
                                  mutation_scale=row["count"] * max_line_width,
                                  color="white", alpha=0.6)
            ax.add_artist(con)

    ax.set_title(f"{team} Pass Network", color="white")
    fig.patch.set_facecolor("black")
    return fig_to_bytes(fig)

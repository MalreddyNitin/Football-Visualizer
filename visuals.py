import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
import seaborn as sns

def plotHeatmap(events_df, player_name, fig=None, ax=None):
    """Draw heatmap of all touches by a player."""
    touches = events_df[
        (events_df["playerName"] == player_name) & (events_df["isTouch"] == True)
    ]

    pitch = VerticalPitch(pitch_type="opta", pitch_color="#121212", line_color="white")
    if fig is None or ax is None:
        fig, ax = pitch.draw(figsize=(10, 7))

    if not touches.empty:
        pitch.kdeplot(
            touches.x, touches.y,
            ax=ax, cmap="Reds", fill=True, levels=50, thresh=0.05
        )
        ax.set_title(f"{player_name} Heatmap", color="white")
        fig.set_facecolor("#121212")
    else:
        ax.text(0.5, 0.5, "No touches found", ha="center", va="center", color="red")

    return fig, ax


def plotPassNetwork(events_df, teamId, fig=None, ax=None):
    """Simple pass network between players of a team."""
    passes = events_df[
        (events_df["teamId"] == teamId) & (events_df["type"] == "Pass")
    ]

    pitch = Pitch(pitch_type="opta", pitch_color="#121212", line_color="white")
    if fig is None or ax is None:
        fig, ax = pitch.draw(figsize=(10, 7))

    for _, row in passes.iterrows():
        pitch.lines(
            row["x"], row["y"], row["endX"], row["endY"],
            color="skyblue", lw=1, ax=ax, comet=True
        )

    ax.set_title("Team Pass Network", color="white")
    fig.set_facecolor("#121212")
    return fig, ax

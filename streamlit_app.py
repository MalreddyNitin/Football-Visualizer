import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

import main   # updated requests+bs4 scraper
import visuals

from mplsoccer import VerticalPitch
import cmasher as cmr
from matplotlib.colors import LinearSegmentedColormap

st.set_page_config(page_title="⚽ Football Analytics Dashboard", layout="wide")
st.title("⚽ Football Analytics Dashboard")

# Sidebar inputs
st.sidebar.header("Input Settings")
url = st.sidebar.text_input("Enter WhoScored Match Link:")

if url:
    try:
        match_data = main.getMatchData(url)
        events_df = main.createEventsDF(match_data)
        matches_df = main.createMatchesDF(match_data)
        matchId = match_data["matchId"]

        # Dropdowns for team selection
        teams = [match_data["home"]["name"], match_data["away"]["name"]]
        selected_team = st.sidebar.selectbox("Select Team", teams)

        # Player list for chosen team
        if selected_team == match_data["home"]["name"]:
            teamId = match_data["home"]["teamId"]
            player_list = [p["name"] for p in match_data["home"]["players"]]
        else:
            teamId = match_data["away"]["teamId"]
            player_list = [p["name"] for p in match_data["away"]["players"]]

        selected_player = st.sidebar.selectbox("Select Player", player_list)

        # Visualization options
        viz_options = [
            "Shotmap (Team)",
            "Pass Network (Team)",
            "Box Passes (Team)",
            "Touchmap (Player)",
            "Heatmap (Player)",
            "Defensive Actions (Player)"
        ]
        selected_viz = st.sidebar.selectbox("Select Visualization", viz_options)

        # Main output
        st.subheader(f"Visualization: {selected_viz}")
        fig = None

        # ---- TEAM LEVEL ----
        if selected_viz == "Shotmap (Team)":
            fig = visuals.createShotmap(
                events_df,
                match_data["home"]["name"],
                match_data["away"]["name"],
                match_data["home"]["teamId"],
                match_data["away"]["teamId"],
                pitchcolor="black",
                shotcolor="white",
                goalcolor="red",
                titlecolor="white",
                legendcolor="white",
                marker_size=300,
            )

        elif selected_viz == "Pass Network (Team)":
            fig = visuals.createPassNetworks(
                match_data,
                events_df,
                matchId,
                selected_team,
                max_line_width=6,
                marker_size=1200,
                edgewidth=3,
                dh_arrow_width=25,
                marker_color="#0e5cba",
                marker_edge_color="w",
                shrink=24,
            )

        elif selected_viz == "Box Passes (Team)":
            fig = visuals.getTeamSuccessfulBoxPasses(
                match_data,
                events_df,
                selected_team,
                pitch_color="#000000",
                cmap="YlGn",
            )

        # ---- PLAYER LEVEL ----
        elif selected_viz == "Touchmap (Player)":
            touch_df = events_df.loc[events_df['teamId'] == teamId].reset_index(drop=True)
            touch_df = touch_df[touch_df.isTouch].reset_index(drop=True)
            touch_df = touch_df[touch_df['playerName'] == selected_player]

            pitch = VerticalPitch(
                pitch_type='opta', half=True,
                pitch_color='#171717', line_color='grey'
            )
            fig, ax = pitch.draw(figsize=(16, 11),
                                 constrained_layout=True, tight_layout=False)

            # Custom colormap for hexbin
            d1 = LinearSegmentedColormap.from_list(
                "Pitch to red", ['#121212', 'red'], N=10
            )

            hexmap = pitch.hexbin(
                touch_df.x, touch_df.y, ax=ax, ec='#171717',
                gridsize=(12, 12), cmap=d1, alpha=0.5, zorder=2, lw=5
            )

            counts = hexmap.get_array()
            verts = hexmap.get_offsets()
            for x, val in zip(verts, counts):
                if x[1] > 47:  # only show in attacking half
                    ax.text(x[0], x[1], s=int(val), c='white',
                            ha='center', va='center', size=14)

            fig.set_facecolor('#171717')

        elif selected_viz == "Heatmap (Player)":
            total_df = events_df.loc[events_df['teamId'] == teamId].reset_index(drop=True)
            total_df = total_df[total_df['playerName'] == selected_player]

            pitch = VerticalPitch(
                pitch_type='opta',
                pitch_color='#121212', line_color='grey', line_zorder=2
            )
            fig, ax = pitch.draw(figsize=(16, 9),
                                 constrained_layout=True, tight_layout=False)

            # Custom colormap
            d1 = LinearSegmentedColormap.from_list(
                "Pitch to red", ['#121212', 'red'], N=10
            )

            if not total_df.empty:
                pitch.kdeplot(total_df.x, total_df.y, ax=ax,
                              cmap=d1, shade=True, levels=100, zorder=1)

            ax.set_title(f"{selected_player} Heatmap", size=15,
                         y=0.99, color='white')
            fig.set_facecolor('#121212')

        elif selected_viz == "Defensive Actions (Player)":
            # ✅ uses your updated visuals.defline
            fig = visuals.defline(events_df, teamId, selected_player)

        # Render figure
        if fig:
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {e}")

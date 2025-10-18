import streamlit as st
import pandas as pd
import json
from visuals import (
    createShotmap,
    createPassNetworks,
    getTeamTotalPasses,
    getTeamSuccessfulBoxPasses,
    createPVFormationMap,
    clusters,
    defline,
)

# ==========================================================
# Page setup
# ==========================================================
st.set_page_config(page_title="⚽ Match Visualizer", layout="wide")
st.title("English Premier League 24/25 Match Visualizer")

# ==========================================================
# Load CSVs and JSON
# ==========================================================
@st.cache_data
def load_data(events_path, teams_path, json_path):
    events_df = pd.read_csv(events_path)
    teams_df = pd.read_csv(teams_path)
    with open(json_path, "r", encoding="utf-8") as f:
        matches = json.load(f)
    return events_df, teams_df, matches


events_path = "events.csv"
teams_path = "teams.csv"
match_data_path = "matches_data.json"

events_df, teams_df, matches = load_data(events_path, teams_path, match_data_path)
#st.sidebar.success(f"Loaded {len(matches)} matches from data.json")

# ==========================================================
# Match selection
# ==========================================================
# match_ids = sorted(events_df["matchId"].unique())
# match_id = st.sidebar.selectbox("Select Match", match_ids)
#

match_ids = sorted(events_df["matchId"].unique().tolist())

# map team_id -> team_name (from teams.csv)
team_name_map = dict(zip(teams_df["team_id"], teams_df["team_name"]))

# map match_id -> "Home vs Away" label (use JSON for home/away order)
id_to_label = {}
for m in matches:
    hid, aid = m["home"]["teamId"], m["away"]["teamId"]
    hname = team_name_map.get(hid, m["home"]["name"])
    aname = team_name_map.get(aid, m["away"]["name"])
    id_to_label[m["matchId"]] = f"{hname} vs {aname}"

match_id = st.sidebar.selectbox(
    "Select Match",
    match_ids,
    format_func=lambda mid: id_to_label.get(mid, str(mid)),
)

# # Match dictionary
this_match = next(m for m in matches if str(m["matchId"]) == str(match_id))
match_data = this_match

# ==========================================================
# Prepare team data
# ==========================================================
match_events = events_df[events_df["matchId"] == match_id].copy()
match_team_ids = match_events["teamId"].unique()

team_names = []
for tid in match_team_ids:
    name = teams_df.loc[teams_df["team_id"] == tid, "team_name"]
    team_names.append(name.iloc[0] if not name.empty else f"Unknown ({tid})")

team_name = st.sidebar.selectbox("Select Team", team_names)
team_id = teams_df.loc[teams_df["team_name"] == team_name, "team_id"].iloc[0]
opponent_names = [t for t in team_names if t != team_name]
opp_name = opponent_names[0] if opponent_names else "Opponent"

opp_id = next((tid for tid in match_team_ids if tid != team_id), None)
st.write(f"### Match {match_id}: {team_name} vs {opp_name}")

# ==========================================================
# Visualization selector
# ==========================================================
viz_choice = st.sidebar.selectbox(
    "Select Visualization Type",
    [
        "Shot Map",
        "Pass Network",
        "Successful Box Passes",
        "Total Passes",
        "PV Formation Map",
        "Pass Clusters",
        "Defensive Line",
    ],
)

team_events = match_events[match_events["teamId"] == team_id].copy()

# ==========================================================
# Visualizations
# ==========================================================
if viz_choice == "Shot Map":
    fig = createShotmap(
        events_df=match_events,
        hometeam=team_name,
        awayteam=opp_name,
        homeid=team_id,
        awayid=opp_id,
        pitchcolor="#171717",
        shotcolor="grey",
        goalcolor="gold",
        titlecolor="white",
        legendcolor="white",
        marker_size=300,
    )
    #st.sidebar.write({
    #   "home shots raw": int((match_events['teamId'] == team_id).sum()),
    #   "shot rows (any team)": int((match_events['type'].astype(str).str.lower().eq('goal') |
    #                                 match_events['type'].astype(str).str.lower().str.contains('shot')).sum()),
    #})
    st.pyplot(fig)

elif viz_choice == "Pass Network":
    fig = createPassNetworks(
        match_data,
        match_events,
        matchId=match_id,
        team=team_name,
        max_line_width=8,
        marker_size=300,
        edgewidth=2,
        dh_arrow_width=15,
        marker_color="#FFDD57",
        marker_edge_color="black",
        shrink=5,
    )
    st.pyplot(fig)

elif viz_choice == "Successful Box Passes":
    fig = getTeamSuccessfulBoxPasses(
        match_data, match_events, team_name, pitch_color="#171717", cmap="plasma"
    )
    st.pyplot(fig)

elif viz_choice == "Total Passes":
    fig = getTeamTotalPasses(
        match_events, team_id, team_name, opp_name, pitch_color="#171717"
    )
    st.pyplot(fig)

elif viz_choice == "PV Formation Map":
    fig = createPVFormationMap(
        match_data,
        match_events,
        team=team_name,
        color_palette="coolwarm",
        markerstyle="o",
        markersize=500,
        markeredgewidth=2,
        labelsize=10,
        labelcolor="white",
    )
    st.pyplot(fig)

elif viz_choice == "Pass Clusters":
    fig = clusters(match_events, team_id)
    st.pyplot(fig)

elif viz_choice == "Defensive Line":
    #player = st.sidebar.text_input("Enter Player Name:")
    #if player:
    #    fig = defline(match_events, team_id, player)
    #    st.pyplot(fig)
    def_players = sorted(
        team_events["playerName"].dropna().unique().tolist()
    )

    if def_players:
        player = st.sidebar.selectbox("Select Player", def_players)
        fig = defline(match_events, team_id, player)
        st.pyplot(fig)
    else:
        st.info("No players found for the selected team in this match.")

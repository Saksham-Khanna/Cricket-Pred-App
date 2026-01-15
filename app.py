import os
import pandas as pd
import streamlit as st

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="AI IPL Team Selector",
    layout="wide"
)

st.title("🏏 AI-Based IPL Team Selector")
st.write("Season-aware player suggestions based on historical performance")

# ------------------ DATA LOADING ------------------
DATA_DIR = "data"

@st.cache_data
def load_data():
    players = pd.read_csv(os.path.join(DATA_DIR, "player_features_with_score.csv"))
    deliveries = pd.read_csv(os.path.join(DATA_DIR, "deliveries.csv"))
    matches = pd.read_csv(os.path.join(DATA_DIR, "matches.csv"))
    return players, deliveries, matches

players_df, deliveries_df, matches_df = load_data()

# ------------------ SIDEBAR INPUTS ------------------
st.sidebar.header("Match Details")

# 1️⃣ Season selection
seasons = sorted(matches_df['season'].dropna().unique(), reverse=True)
selected_season = st.sidebar.selectbox("Select IPL Season", seasons)

# Filter matches by season
season_matches = matches_df[matches_df['season'] == selected_season]
season_match_ids = season_matches['id'].unique()

# Filter deliveries by season
season_deliveries = deliveries_df[
    deliveries_df['match_id'].isin(season_match_ids)
]

# 2️⃣ Team selection (season-aware)
teams = sorted(
    pd.unique(
        season_matches[['team1', 'team2']].values.ravel()
    )
)

team_a = st.sidebar.selectbox("Select Team A", teams)
team_b = st.sidebar.selectbox("Select Team B", teams)

# ------------------ PLAYER SUGGESTION LOGIC ------------------
def suggest_players(team_a, team_b, season_deliveries, players_df, top_n=22):
    # Player → team mapping for the selected season
    player_team_map = (
        season_deliveries[['batter', 'batting_team']]
        .drop_duplicates()
        .rename(columns={
            'batter': 'player',
            'batting_team': 'team'
        })
    )

    # Merge with player features
    players_with_team = players_df.merge(
        player_team_map,
        on='player',
        how='inner'
    )

    # Filter players belonging to the two teams
    eligible_players = players_with_team[
        (players_with_team['team'] == team_a) |
        (players_with_team['team'] == team_b)
    ].copy()

    # Final score = performance score only (no venue logic)
    eligible_players['final_score'] = eligible_players['performance_score']

    # Rank players
    suggested = eligible_players.sort_values(
        'final_score',
        ascending=False
    ).head(top_n)

    return suggested.reset_index(drop=True)

# ------------------ BUTTON ACTION ------------------
if st.sidebar.button("Suggest Players"):
    if team_a == team_b:
        st.error("Team A and Team B must be different.")
    else:
        suggestions = suggest_players(
            team_a,
            team_b,
            season_deliveries,
            players_df
        )

        st.subheader(
            f"Top {len(suggestions)} Suggested Players "
            f"({team_a} vs {team_b}, IPL {selected_season})"
        )

        st.dataframe(
            suggestions[['player', 'team', 'final_score']],
            use_container_width=True
        )

        st.success("Player suggestions generated successfully!")

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption(
    "AI IPL Team Selector | "
    "Season-aware, team-based, data-driven (no venue assumptions)"
)

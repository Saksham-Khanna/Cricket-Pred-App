import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ================= PAGE CONFIG =================
st.set_page_config(page_title="AI IPL Player Analytics", layout="wide")
st.title("🏏 AI-Based IPL Player Analytics")
st.markdown("Season-aware AI-driven player suggestions & intelligent comparison dashboard")

DATA_DIR = "data"

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    players = pd.read_csv(os.path.join(DATA_DIR, "player_features_with_score.csv"))
    deliveries = pd.read_csv(os.path.join(DATA_DIR, "deliveries.csv"))
    matches = pd.read_csv(os.path.join(DATA_DIR, "matches.csv"))
    return players, deliveries, matches

players_df, deliveries_df, matches_df = load_data()

# ================= SESSION STATE =================
if "selected_season" not in st.session_state:
    st.session_state.selected_season = None

if "suggestions_df" not in st.session_state:
    st.session_state.suggestions_df = None

# ================= HELPER FUNCTIONS =================
@st.cache_data
def get_season_data(season):
    season_matches = matches_df[matches_df["season"] == season]
    match_ids = season_matches["id"].unique()

    season_deliveries = deliveries_df[
        deliveries_df["match_id"].isin(match_ids)
    ]

    player_team_map = (
        season_deliveries[["batter", "batting_team"]]
        .drop_duplicates()
        .rename(columns={"batter": "player", "batting_team": "team"})
    )

    players_season = players_df.merge(player_team_map, on="player", how="inner")
    return season_matches, players_season


def suggest_players(df, team_a, team_b, n):
    eligible = df[df["team"].isin([team_a, team_b])].copy()
    eligible["final_score"] = eligible["performance_score"]
    return (
        eligible.sort_values("final_score", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )

# ================= SIDEBAR =================
st.sidebar.header("Season Selection")

seasons = sorted(matches_df["season"].dropna().unique(), reverse=True)
selected_season = st.sidebar.selectbox("Select IPL Season", seasons)

# Reset suggestions only when season changes
if st.session_state.selected_season != selected_season:
    st.session_state.selected_season = selected_season
    st.session_state.suggestions_df = None

season_matches, players_season_df = get_season_data(selected_season)

# ================= TABS =================
tab1, tab2 = st.tabs(["🏏 Suggest Players", "🔍 Compare Players"])

# =================================================
# 🟢 TAB 1 — AI PLAYER SUGGESTION ENGINE
# =================================================
with tab1:
    st.subheader("🏏 AI Player Suggestion Engine")

    teams = sorted(
        pd.unique(season_matches[["team1", "team2"]].values.ravel())
    )

    with st.form("suggestion_form"):

        col1, col2 = st.columns(2)
        with col1:
            team_a = st.selectbox("Select Team A", teams)
        with col2:
            team_b = st.selectbox("Select Team B", teams)

        eligible = players_season_df[
            players_season_df["team"].isin([team_a, team_b])
        ]

        max_available = len(eligible)

        if max_available > 0:
            top_n = st.number_input(
                "Enter number of players to suggest",
                min_value=1,
                max_value=max_available,
                value=1,
                step=1
            )
        else:
            top_n = 1

        submitted = st.form_submit_button("Generate AI Suggestions")

        if submitted:
            if team_a == team_b:
                st.error("Teams must be different.")
            elif max_available == 0:
                st.warning("No eligible players.")
            else:
                st.session_state.suggestions_df = suggest_players(
                    players_season_df, team_a, team_b, top_n
                )

    # Display results
    if st.session_state.suggestions_df is None:
        st.info("Select teams and generate suggestions.")
    else:
        result = st.session_state.suggestions_df

        st.markdown("### 📊 Key Insights")
        c1, c2, c3 = st.columns(3)
        c1.metric("Players Selected", len(result))
        c2.metric("Top Score", round(result["final_score"].max(), 2))
        c3.metric("Average Score", round(result["final_score"].mean(), 2))

        st.success(f"🔥 Best AI Pick: {result.iloc[0]['player']}")

        st.markdown("### 🏆 Suggested Players")
        st.dataframe(
            result[["player", "team", "final_score"]],
            use_container_width=True
        )

        # ===== Premium Horizontal Chart =====
        st.markdown("### 📈 Performance Visualization")

        fig, ax = plt.subplots(figsize=(10, 6))

        players = result["player"][::-1]
        scores = result["final_score"][::-1]

        bars = ax.barh(players, scores, height=0.35, color="#4C78A8")
        bars[-1].set_color("gold")

        ax.set_xlabel("Performance Score")
        ax.set_title("Top Player Performance Comparison")

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='x', linestyle='--', alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)

# =================================================
# 🟢 TAB 2 — INTELLIGENT PLAYER COMPARISON
# =================================================
with tab2:
    st.subheader("🔍 Player Performance Comparison")

    teams_available = sorted(players_season_df["team"].unique())

    col1, col2 = st.columns(2)

    with col1:
        team_1 = st.selectbox("Select Team 1", teams_available)
        players_team_1 = sorted(
            players_season_df[players_season_df["team"] == team_1]["player"].unique()
        )
        player_1 = st.selectbox("Select Player 1", players_team_1)

    with col2:
        team_2 = st.selectbox("Select Team 2", teams_available, index=1)
        players_team_2 = sorted(
            players_season_df[players_season_df["team"] == team_2]["player"].unique()
        )
        player_2 = st.selectbox("Select Player 2", players_team_2)

    if team_1 == team_2 and player_1 == player_2:
        st.warning("Please select two different players.")
    else:
        p1 = players_season_df[
            (players_season_df["team"] == team_1) &
            (players_season_df["player"] == player_1)
        ].iloc[0]

        p2 = players_season_df[
            (players_season_df["team"] == team_2) &
            (players_season_df["player"] == player_2)
        ].iloc[0]

        comparison_df = pd.DataFrame({
            "Metric": ["Team", "Runs (Batting)", "Wickets (Bowling)", "Performance Score"],
            player_1: [
                p1["team"],
                p1["runs"],
                p1["wickets"],
                round(p1["performance_score"], 3)
            ],
            player_2: [
                p2["team"],
                p2["runs"],
                p2["wickets"],
                round(p2["performance_score"], 3)
            ],
        })

        st.dataframe(comparison_df, use_container_width=True)

        st.markdown("### 🧠 Performance Insights")

        # Batting
        if p1["runs"] > p2["runs"]:
            st.success(f"🏏 Better Batting: {player_1}")
        elif p2["runs"] > p1["runs"]:
            st.success(f"🏏 Better Batting: {player_2}")
        else:
            st.info("🏏 Batting Performance: Equal")

        # Bowling
        if p1["wickets"] > p2["wickets"]:
            st.success(f"🎯 Better Bowling: {player_1}")
        elif p2["wickets"] > p1["wickets"]:
            st.success(f"🎯 Better Bowling: {player_2}")
        else:
            st.info("🎯 Bowling Performance: Equal")

        # Overall
        if p1["performance_score"] > p2["performance_score"]:
            st.success(f"🏆 Better Overall Performance: {player_1}")
        elif p2["performance_score"] > p1["performance_score"]:
            st.success(f"🏆 Better Overall Performance: {player_2}")
        else:
            st.info("🏆 Overall Performance: Equal")

# ================= FOOTER =================
st.markdown("---")
st.caption("AI IPL Player Analytics | Season-aware • Data-driven • Resume-ready")

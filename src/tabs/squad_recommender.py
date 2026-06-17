import os
from datetime import date

import streamlit as st

from src import db
from src.ai import recommender


def render():
    st.header("Squad Recommender")
    st.caption("AI-powered squad selection balancing fairness and performance.")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.warning(
            "**ANTHROPIC_API_KEY not set.** Add it to a `.env` file in the project root "
            "to enable AI recommendations. See `.env.example` for the format."
        )

    all_fixtures = db.get_fixtures()
    today_str = str(date.today())
    upcoming = [f for f in all_fixtures if f["date"] >= today_str]

    if not upcoming:
        st.info(
            "No upcoming fixtures found. Add fixtures in the **Games → Upcoming Fixtures** tab first."
        )
        return

    fixture_labels = {
        f"{f['date']} — vs {f['opponent']} ({f['match_type']}, {f.get('squad') or 'squad TBD'})": f
        for f in upcoming
    }

    selected_label = st.selectbox("Select Upcoming Fixture", list(fixture_labels.keys()))
    fixture = fixture_labels[selected_label]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Opponent", fixture["opponent"])
    c2.metric("Match Type", fixture["match_type"])
    c3.metric("Squad", fixture.get("squad") or "TBD")
    c4.metric("Location", fixture.get("location") or "TBD")
    c5.metric("Opposition", fixture.get("opposition_strength") or "Medium")

    st.divider()

    player_stats = db.get_player_stats()
    if not player_stats:
        st.warning("No players in the database. Import player data from the sidebar first.")
        return

    coach_notes = st.text_area(
        "Coach Notes (optional)",
        placeholder="e.g. Jamie just back from injury — ease him in. We need to win this one for the league.",
        height=80,
    )

    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.caption(
            f"Analysing {len(player_stats)} players. "
            "The AI will balance fairness, player tier, and opposition strength."
        )
    with col_btn:
        generate = st.button(
            "Generate Squad",
            type="primary",
            use_container_width=True,
            disabled=not api_key,
        )

    if generate:
        if not api_key:
            st.error("Cannot generate — ANTHROPIC_API_KEY is not set.")
            return
        recent_games = db.get_games()[:5]
        with st.spinner("Analysing squad and generating recommendation..."):
            try:
                recommendation = recommender.generate_squad(
                    fixture, player_stats, recent_games, coach_notes=coach_notes
                )
            except Exception as e:
                st.error(f"Error generating recommendation: {e}")
                return

        st.subheader("AI Recommendation")
        st.markdown(recommendation)

        st.divider()
        st.caption("This recommendation is a starting point. The coach makes the final call.")

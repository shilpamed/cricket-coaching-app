from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from src.data_loader import import_cricket_csv, import_players_csv
from src.db import init_db
from src.tabs import games, insights, players, squad_recommender

st.set_page_config(
    page_title="HH Cricket Coaching",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Cricket green theme ─────────────────────────────── */
[data-testid="stAppViewContainer"] > .main {
    background-color: #f5f9f5;
}
[data-testid="stSidebar"] {
    background-color: #163d16;
}

/* Sidebar text — force white on dark green */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] div {
    color: #e8f5e8 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}

/* Sidebar expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color: #1f5c1f;
    border: 1px solid #2d7a2d;
    border-radius: 8px;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #e8f5e8 !important;
}

/* Sidebar divider */
[data-testid="stSidebar"] hr {
    border-color: #2d7a2d;
}

/* Sidebar file uploader */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background-color: #1f5c1f;
    border-radius: 6px;
}

/* Primary buttons */
[data-testid="baseButton-primary"] {
    background-color: #1e7a1e !important;
    border-color: #1e7a1e !important;
    color: white !important;
}
[data-testid="baseButton-primary"]:hover {
    background-color: #155a15 !important;
    border-color: #155a15 !important;
}

/* Active tab underline */
[data-baseweb="tab-highlight"] {
    background-color: #1e7a1e !important;
}
[data-baseweb="tab"][aria-selected="true"] p {
    color: #1e7a1e !important;
    font-weight: 600;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 14px 18px !important;
    border-left: 4px solid #1e7a1e;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
[data-testid="stMetricValue"] {
    color: #1a5c1a !important;
    font-size: 1.8rem !important;
}

/* Headings */
h1, h2, h3 {
    color: #1a5c1a;
}

/* Sidebar heading — white on dark green */
[data-testid="stSidebar"] h1 {
    color: #ffffff !important;
}

/* Divider */
hr {
    border-color: #c8e6c8;
}
</style>
""", unsafe_allow_html=True)

init_db()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏏 HH Cricket")
    st.caption("U11 Coaching Dashboard")
    st.divider()

    with st.expander("📥 Import Data"):
        st.markdown("**Historical Games & Players**")
        st.caption("Upload the CricketTest-style CSV (date / match / opponent / players…)")
        games_file = st.file_uploader("Games CSV", type=["csv"], key="import_games_csv")
        if games_file:
            if st.button("Import Games & Players", key="do_import_games"):
                with st.spinner("Importing…"):
                    msg = import_cricket_csv(games_file)
                st.success(msg)
                st.rerun()

        st.divider()
        st.markdown("**Players Only**")
        st.caption("Required column: `name`. Optional: `preferred_squad`, ratings, etc.")
        players_file = st.file_uploader("Players CSV", type=["csv"], key="import_players_csv")
        if players_file:
            if st.button("Import Players", key="do_import_players"):
                with st.spinner("Importing…"):
                    msg = import_players_csv(players_file)
                st.success(msg)
                st.rerun()

    with st.expander("📋 Download Templates"):
        players_tpl = (
            "name,preferred_squad,batting_rating,bowling_rating,fielding_rating,"
            "bowling_type,preferred_batting_position,notes\n"
            "John Smith,U11 Sunday,7,5,6,Pace,Top,\n"
            "Jane Doe,U11 Tuesday,6,7,5,Spin,Middle,\n"
        )
        st.download_button(
            "Players Template (CSV)",
            players_tpl,
            file_name="players_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["👤 Players", "🏏 Games", "📊 Insights", "🤖 Squad Recommender"]
)

with tab1:
    players.render()

with tab2:
    games.render()

with tab3:
    insights.render()

with tab4:
    squad_recommender.render()

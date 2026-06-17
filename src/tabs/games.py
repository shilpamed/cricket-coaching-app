from datetime import date

import streamlit as st

from src import db

SQUAD_COLORS = {
    "U11 Sunday": "#2980b9",
    "U11 Tuesday": "#27ae60",
    "U12": "#e67e22",
}
RESULT_COLORS = {"W": "#27ae60", "L": "#e74c3c", "D": "#7f8c8d"}
RESULT_LABELS = {"W": "Won", "L": "Lost", "D": "Draw"}


def _squad_color(squad: str | None) -> str:
    return SQUAD_COLORS.get(squad or "", "#95a5a6")


def _render_game_cards(games_list: list) -> None:
    for g in games_list:
        squad = g.get("squad") or None
        sc = _squad_color(squad)
        squad_label = squad or "Unknown"
        result = g.get("result") or None
        rc = RESULT_COLORS.get(result, "#bdc3c7")
        rl = RESULT_LABELS.get(result, "—")

        score_html = ""
        if g.get("our_score") and g.get("opponent_score"):
            score_html = f'<span style="font-size:12px;color:#555;">{g["our_score"]} – {g["opponent_score"]}</span>'

        st.markdown(
            f"""
<div style="background:white;border-radius:10px;padding:14px 18px;
    border-left:4px solid {sc};box-shadow:0 1px 3px rgba(0,0,0,0.07);
    margin-bottom:8px;font-family:sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-size:11px;color:#888;margin-bottom:4px;">{g["date"]} · {g["match_type"]}</div>
      <div style="font-size:16px;font-weight:700;color:#1a1a1a;">vs {g["opponent"]}</div>
      <div style="margin-top:6px;">
        <span style="background:{sc};color:white;padding:2px 8px;
            border-radius:10px;font-size:10px;">{squad_label}</span>
        &nbsp;
        <span style="background:#ecf0f1;color:#555;padding:2px 8px;
            border-radius:10px;font-size:10px;">{g.get("age_group") or "—"}</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="background:{rc};color:white;padding:4px 14px;border-radius:16px;
          font-weight:700;font-size:14px;display:inline-block;">{rl}</div>
      <div style="margin-top:6px;">{score_html}</div>
    </div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )


def _render_fixture_cards(fixtures_list: list) -> None:
    for f in fixtures_list:
        squad = f.get("squad") or None
        sc = _squad_color(squad)
        squad_label = squad or "Unknown"
        delta = (date.fromisoformat(f["date"]) - date.today()).days
        days_text = "Today" if delta == 0 else f"In {delta} day{'s' if delta != 1 else ''}"
        urgency_color = "#e74c3c" if delta <= 3 else "#e67e22" if delta <= 7 else "#27ae60"

        location = f.get("location") or ""
        loc_html = f'<span style="font-size:11px;color:#888;">📍 {location}</span>' if location else ""

        st.markdown(
            f"""
<div style="background:white;border-radius:10px;padding:14px 18px;
    border-left:4px solid {sc};box-shadow:0 1px 3px rgba(0,0,0,0.07);
    margin-bottom:8px;font-family:sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-size:11px;color:#888;margin-bottom:4px;">{f["date"]} · {f["match_type"]}</div>
      <div style="font-size:16px;font-weight:700;color:#1a1a1a;">vs {f["opponent"]}</div>
      <div style="margin-top:6px;">
        <span style="background:{sc};color:white;padding:2px 8px;
            border-radius:10px;font-size:10px;">{squad_label}</span>
        &nbsp;
        {loc_html}
      </div>
    </div>
    <div style="text-align:right;">
      <div style="background:{urgency_color};color:white;padding:4px 12px;border-radius:16px;
          font-weight:600;font-size:12px;display:inline-block;">🕐 {days_text}</div>
    </div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )


MATCH_TYPES = [
    "U11 North", "U11 South", "U11 Friendly",
    "U12 North div 3", "U12 Friendly", "U12 Tournament",
    "Pre-season Friendly", "Other",
]
AGE_GROUPS = ["U11", "U12", "Other"]
SQUADS = ["U11 Sunday", "U11 Tuesday", "U12"]
RESULTS = ["", "W", "L", "D"]
OPPOSITION_STRENGTHS = ["Strong", "Medium", "Weak"]


def _derive_competition(match_type: str) -> str:
    mt = match_type.lower()
    if "north" in mt:
        return "North"
    if "south" in mt:
        return "South"
    if "friendly" in mt:
        return "Friendly"
    if "tournament" in mt:
        return "Tournament"
    if "pre" in mt:
        return "Pre-season"
    return "Other"


# ── Game Dialogs ──────────────────────────────────────────────────────────────

@st.dialog("Add Game", width="large")
def _add_game_dialog():
    all_players = db.get_players()
    player_options = {p["name"]: p["id"] for p in all_players}

    with st.form("add_game_form"):
        c1, c2 = st.columns(2)
        game_date = c1.date_input("Date *", value=date.today())
        opponent = c2.text_input("Opponent *")

        c3, c4 = st.columns(2)
        match_type = c3.selectbox("Match Type", MATCH_TYPES)
        squad = c4.selectbox("Squad", SQUADS)

        c5, c6, c7 = st.columns(3)
        age_group = c5.selectbox("Age Group", AGE_GROUPS)
        location = c6.text_input("Location")
        opp_strength = c7.selectbox("Opposition Strength", OPPOSITION_STRENGTHS, index=1)

        c8, c9, c10 = st.columns(3)
        result = c8.selectbox("Result", RESULTS, format_func=lambda x: "— not recorded" if x == "" else x)
        our_score = c9.text_input("Our Score")
        opp_score = c10.text_input("Opponent Score")

        st.markdown("**Player Selection**")
        played_names = st.multiselect("Players who played", list(player_options.keys()))
        invited_names = st.multiselect("Invited but couldn't play", list(player_options.keys()))

        submitted = st.form_submit_button("Add Game", type="primary")

    if submitted:
        if not opponent.strip():
            st.error("Opponent is required.")
            return
        game_id = db.upsert_game(
            date_val=game_date,
            opponent=opponent.strip(),
            match_type=match_type,
            age_group=age_group,
            competition=_derive_competition(match_type),
            squad=squad,
            location=location,
            opposition_strength=opp_strength,
            result=result or None,
            our_score=our_score or None,
            opponent_score=opp_score or None,
        )
        played_ids = [player_options[n] for n in played_names if n in player_options]
        invited_ids = [
            player_options[n] for n in invited_names
            if n in player_options and n not in played_names
        ]
        db.set_game_players(game_id, played_ids, invited_ids)
        st.success(f"Game added: vs {opponent.strip()}")
        st.rerun()


@st.dialog("Edit Game", width="large")
def _edit_game_dialog(game_id: int):
    game = db.get_game(game_id)
    if not game:
        st.error("Game not found.")
        return

    all_players = db.get_players()
    player_options = {p["name"]: p["id"] for p in all_players}

    current = db.get_game_players(game_id)
    played_ids_cur = [r["player_id"] for r in current if r["status"] == "played"]
    invited_ids_cur = [r["player_id"] for r in current if r["status"] == "invited"]

    mt_idx = MATCH_TYPES.index(game["match_type"]) if game["match_type"] in MATCH_TYPES else len(MATCH_TYPES) - 1
    sq_idx = SQUADS.index(game["squad"]) if game.get("squad") in SQUADS else 0
    ag_idx = AGE_GROUPS.index(game["age_group"]) if game["age_group"] in AGE_GROUPS else 0
    res_idx = RESULTS.index(game.get("result") or "") if (game.get("result") or "") in RESULTS else 0
    os_val = game.get("opposition_strength") or "Medium"
    os_idx = OPPOSITION_STRENGTHS.index(os_val) if os_val in OPPOSITION_STRENGTHS else 1

    with st.form("edit_game_form"):
        c1, c2 = st.columns(2)
        game_date = c1.date_input("Date *", value=date.fromisoformat(game["date"]))
        opponent = c2.text_input("Opponent *", value=game["opponent"])

        c3, c4 = st.columns(2)
        match_type = c3.selectbox("Match Type", MATCH_TYPES, index=mt_idx)
        squad = c4.selectbox("Squad", SQUADS, index=sq_idx)

        c5, c6, c7 = st.columns(3)
        age_group = c5.selectbox("Age Group", AGE_GROUPS, index=ag_idx)
        location = c6.text_input("Location", value=game.get("location") or "")
        opp_strength = c7.selectbox("Opposition Strength", OPPOSITION_STRENGTHS, index=os_idx)

        c8, c9, c10 = st.columns(3)
        result = c8.selectbox("Result", RESULTS, index=res_idx, format_func=lambda x: "— not recorded" if x == "" else x)
        our_score = c9.text_input("Our Score", value=game.get("our_score") or "")
        opp_score = c10.text_input("Opponent Score", value=game.get("opponent_score") or "")

        st.markdown("**Player Selection**")
        played_names = st.multiselect(
            "Players who played",
            list(player_options.keys()),
            default=[p["name"] for p in all_players if p["id"] in played_ids_cur],
        )
        invited_names = st.multiselect(
            "Invited but couldn't play",
            list(player_options.keys()),
            default=[p["name"] for p in all_players if p["id"] in invited_ids_cur],
        )

        submitted = st.form_submit_button("Save Changes", type="primary")

    if submitted:
        if not opponent.strip():
            st.error("Opponent is required.")
            return
        db.upsert_game(
            date_val=game_date,
            opponent=opponent.strip(),
            match_type=match_type,
            age_group=age_group,
            competition=_derive_competition(match_type),
            squad=squad,
            location=location,
            opposition_strength=opp_strength,
            result=result or None,
            our_score=our_score or None,
            opponent_score=opp_score or None,
            game_id=game_id,
        )
        played_ids = [player_options[n] for n in played_names if n in player_options]
        invited_ids = [
            player_options[n] for n in invited_names
            if n in player_options and n not in played_names
        ]
        db.set_game_players(game_id, played_ids, invited_ids)
        st.success("Game updated!")
        st.rerun()


@st.dialog("Confirm Delete Game", width="small")
def _confirm_delete_game_dialog(game_id: int, label: str):
    st.warning(f"Delete game: **{label}**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes, Delete", type="primary", use_container_width=True):
        db.delete_game(game_id)
        st.rerun()
    if c2.button("Cancel", use_container_width=True):
        st.rerun()


# ── Fixture Dialogs ───────────────────────────────────────────────────────────

@st.dialog("Add Fixture", width="large")
def _add_fixture_dialog():
    with st.form("add_fixture_form"):
        c1, c2 = st.columns(2)
        fix_date = c1.date_input("Date *", value=date.today())
        opponent = c2.text_input("Opponent *")

        c3, c4 = st.columns(2)
        match_type = c3.selectbox("Match Type", MATCH_TYPES)
        squad = c4.selectbox("Squad", SQUADS)

        c5, c6 = st.columns(2)
        age_group = c5.selectbox("Age Group", AGE_GROUPS)
        location = c6.text_input("Location")

        submitted = st.form_submit_button("Add Fixture", type="primary")

    if submitted:
        if not opponent.strip():
            st.error("Opponent is required.")
            return
        db.upsert_fixture(
            date_val=fix_date,
            opponent=opponent.strip(),
            match_type=match_type,
            age_group=age_group,
            competition=_derive_competition(match_type),
            squad=squad,
            location=location,
        )
        st.success(f"Fixture added: vs {opponent.strip()}")
        st.rerun()


@st.dialog("Edit Fixture", width="large")
def _edit_fixture_dialog(fixture_id: int):
    fixture = db.get_fixture(fixture_id)
    if not fixture:
        st.error("Fixture not found.")
        return

    mt_idx = MATCH_TYPES.index(fixture["match_type"]) if fixture["match_type"] in MATCH_TYPES else len(MATCH_TYPES) - 1
    sq_idx = SQUADS.index(fixture["squad"]) if fixture.get("squad") in SQUADS else 0
    ag_idx = AGE_GROUPS.index(fixture["age_group"]) if fixture["age_group"] in AGE_GROUPS else 0

    with st.form("edit_fixture_form"):
        c1, c2 = st.columns(2)
        fix_date = c1.date_input("Date *", value=date.fromisoformat(fixture["date"]))
        opponent = c2.text_input("Opponent *", value=fixture["opponent"])

        c3, c4 = st.columns(2)
        match_type = c3.selectbox("Match Type", MATCH_TYPES, index=mt_idx)
        squad = c4.selectbox("Squad", SQUADS, index=sq_idx)

        c5, c6 = st.columns(2)
        age_group = c5.selectbox("Age Group", AGE_GROUPS, index=ag_idx)
        location = c6.text_input("Location", value=fixture.get("location") or "")

        submitted = st.form_submit_button("Save Changes", type="primary")

    if submitted:
        if not opponent.strip():
            st.error("Opponent is required.")
            return
        db.upsert_fixture(
            date_val=fix_date,
            opponent=opponent.strip(),
            match_type=match_type,
            age_group=age_group,
            competition=_derive_competition(match_type),
            squad=squad,
            location=location,
            fixture_id=fixture_id,
        )
        st.success("Fixture updated!")
        st.rerun()


@st.dialog("Confirm Delete Fixture", width="small")
def _confirm_delete_fixture_dialog(fixture_id: int, label: str):
    st.warning(f"Delete fixture: **{label}**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes, Delete", type="primary", use_container_width=True):
        db.delete_fixture(fixture_id)
        st.rerun()
    if c2.button("Cancel", use_container_width=True):
        st.rerun()


# ── Tab Sections ──────────────────────────────────────────────────────────────

def _render_past_games():
    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("+ Add Game", type="primary", use_container_width=True, key="add_game_btn"):
            _add_game_dialog()

    games = db.get_games()

    if not games:
        st.info("No games recorded yet. Add a game above or import via the sidebar.")
        return

    c1, c2 = st.columns(2)
    squad_filter = c1.selectbox("Filter by Squad", ["All"] + SQUADS, key="past_squad_f")
    ag_filter = c2.selectbox("Filter by Age Group", ["All"] + AGE_GROUPS, key="past_ag_f")

    filtered = games
    if squad_filter != "All":
        filtered = [g for g in filtered if g.get("squad") == squad_filter]
    if ag_filter != "All":
        filtered = [g for g in filtered if g.get("age_group") == ag_filter]

    if not filtered:
        st.info("No games match the current filter.")
        return

    _render_game_cards(filtered)

    st.divider()
    st.subheader("Edit / Delete Game")

    game_labels = [f"{g['date']} — vs {g['opponent']} ({g['match_type']})" for g in filtered]
    selected_label = st.selectbox("Select game", ["—"] + game_labels, key="sel_edit_game")

    if selected_label != "—":
        idx = game_labels.index(selected_label)
        sel_game = filtered[idx]

        selections = db.get_game_players(sel_game["id"])
        if selections:
            played = sorted(s["player_name"] for s in selections if s["status"] == "played")
            invited = sorted(s["player_name"] for s in selections if s["status"] == "invited")
            if played:
                st.caption(f"Played ({len(played)}): {', '.join(played)}")
            if invited:
                st.caption(f"Invited, couldn't play ({len(invited)}): {', '.join(invited)}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit Game", type="primary", use_container_width=True, key="edit_game_btn"):
                _edit_game_dialog(sel_game["id"])
        with c2:
            if st.button("Delete Game", use_container_width=True, key="del_game_btn"):
                _confirm_delete_game_dialog(
                    sel_game["id"],
                    f"{sel_game['date']} vs {sel_game['opponent']}"
                )


def _render_upcoming_fixtures():
    col_info, col_btn = st.columns([5, 1])
    col_info.caption("Upcoming fixtures are games added with a future date.")
    with col_btn:
        if st.button("+ Add Game", type="primary", use_container_width=True, key="add_fix_btn"):
            _add_game_dialog()

    fixtures = db.get_fixtures()

    if not fixtures:
        st.info("No upcoming games found. Add a game with a future date to see it here.")
        return

    squad_filter = st.selectbox("Filter by Squad", ["All"] + SQUADS, key="fix_squad_f")

    filtered = fixtures
    if squad_filter != "All":
        filtered = [f for f in filtered if f.get("squad") == squad_filter]

    if not filtered:
        st.info("No upcoming fixtures match the current filter.")
        return

    _render_fixture_cards(filtered)

    st.divider()
    st.subheader("Edit / Delete Upcoming Game")

    fix_labels = [f"{f['date']} — vs {f['opponent']} ({f['match_type']})" for f in filtered]
    selected_label = st.selectbox("Select game", ["—"] + fix_labels, key="sel_edit_fix")

    if selected_label != "—":
        idx = fix_labels.index(selected_label)
        sel_fix = filtered[idx]

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit Game", type="primary", use_container_width=True, key="edit_fix_btn"):
                _edit_game_dialog(sel_fix["id"])
        with c2:
            if st.button("Delete Game", use_container_width=True, key="del_fix_btn"):
                _confirm_delete_game_dialog(
                    sel_fix["id"],
                    f"{sel_fix['date']} vs {sel_fix['opponent']}"
                )


def render():
    st.header("Games")
    tab_past, tab_upcoming = st.tabs(["Past Games", "Upcoming Fixtures"])
    with tab_past:
        _render_past_games()
    with tab_upcoming:
        _render_upcoming_fixtures()

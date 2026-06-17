import streamlit as st

from src import db

SQUADS = ["", "U11 Sunday", "U11 Tuesday", "U12"]
BOWLING_TYPES = ["None", "Pace", "Spin"]
BAT_POSITIONS = ["Top", "Middle", "Lower"]
TIERS = ["Strong", "Medium", "Developmental"]
PRIMARY_STRENGTHS = ["All-rounder", "Batting", "Bowling"]

SQUAD_COLORS = {
    "U11 Sunday": "#2980b9",
    "U11 Tuesday": "#27ae60",
    "U12": "#e67e22",
}
TIER_COLORS = {
    "Strong": "#1a7a2e",
    "Medium": "#2980b9",
    "Developmental": "#8e44ad",
}


def _squad_color(squad: str | None) -> str:
    return SQUAD_COLORS.get(squad or "", "#95a5a6")


def _render_player_cards(players: list) -> None:
    for i in range(0, len(players), 3):
        cols = st.columns(3)
        for j, p in enumerate(players[i : i + 3]):
            with cols[j]:
                name = p["name"]
                squad = p.get("preferred_squad") or None
                tier = p.get("tier") or "Medium"
                bat = int(p["batting_rating"] or 5)
                bowl = int(p["bowling_rating"] or 5)
                field = int(p["fielding_rating"] or 5)
                played = p["games_played"]
                last = p["last_game_date"] or "Never"
                strength = p.get("primary_strength") or "All-rounder"

                initials = "".join(w[0].upper() for w in name.split()[:2])
                sc = _squad_color(squad)
                tc = TIER_COLORS.get(tier, "#95a5a6")
                squad_label = squad or "No Squad"

                st.markdown(
                    f"""
<div style="background:white;border-radius:10px;padding:14px 16px;
    border-left:4px solid {sc};box-shadow:0 1px 4px rgba(0,0,0,0.08);
    margin-bottom:8px;font-family:sans-serif;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
    <div style="width:40px;height:40px;border-radius:50%;background:{sc};
        color:white;display:flex;align-items:center;justify-content:center;
        font-weight:700;font-size:13px;flex-shrink:0;">{initials}</div>
    <div>
      <div style="font-weight:600;font-size:14px;color:#1a1a1a;">{name}</div>
      <div style="margin-top:3px;">
        <span style="background:{sc};color:white;padding:1px 7px;
            border-radius:10px;font-size:10px;">{squad_label}</span>
        &nbsp;
        <span style="background:{tc};color:white;padding:1px 7px;
            border-radius:10px;font-size:10px;">{tier}</span>
      </div>
    </div>
  </div>
  <div style="font-size:11px;color:#555;margin-bottom:4px;">
    <div style="display:flex;justify-content:space-between;">
      <span>🏏 Bat</span><span style="font-weight:600;color:#2980b9;">{bat}/10</span>
    </div>
    <div style="height:4px;background:#eee;border-radius:2px;margin:3px 0 7px;">
      <div style="height:4px;background:#2980b9;border-radius:2px;width:{bat * 10}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;">
      <span>🎯 Bowl</span><span style="font-weight:600;color:#e67e22;">{bowl}/10</span>
    </div>
    <div style="height:4px;background:#eee;border-radius:2px;margin:3px 0 7px;">
      <div style="height:4px;background:#e67e22;border-radius:2px;width:{bowl * 10}%;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;">
      <span>⚡ Field</span><span style="font-weight:600;color:#27ae60;">{field}/10</span>
    </div>
    <div style="height:4px;background:#eee;border-radius:2px;margin:3px 0 7px;">
      <div style="height:4px;background:#27ae60;border-radius:2px;width:{field * 10}%;"></div>
    </div>
  </div>
  <div style="margin-top:6px;font-size:11px;color:#777;
      display:flex;justify-content:space-between;border-top:1px solid #f0f0f0;padding-top:8px;">
    <span>🎮 <strong>{played}</strong> played</span>
    <span style="color:#999;">{strength}</span>
    <span>📅 {last}</span>
  </div>
</div>""",
                    unsafe_allow_html=True,
                )


@st.dialog("Add Player", width="large")
def _add_player_dialog():
    with st.form("add_player_form"):
        name = st.text_input("Name *")
        preferred_squad = st.selectbox(
            "Preferred Squad", SQUADS,
            format_func=lambda x: "No preference" if x == "" else x,
        )
        c1, c2 = st.columns(2)
        tier = c1.selectbox("Player Tier", TIERS, index=1)
        primary_strength = c2.selectbox("Primary Strength", PRIMARY_STRENGTHS)
        c3, c4, c5 = st.columns(3)
        batting = c3.slider("Batting Rating", 1, 10, 5)
        bowling = c4.slider("Bowling Rating", 1, 10, 5)
        fielding = c5.slider("Fielding Rating", 1, 10, 5)
        bowling_type = st.selectbox("Bowling Type", BOWLING_TYPES)
        bat_pos = st.selectbox("Batting Position", BAT_POSITIONS, index=1)
        notes = st.text_area("Notes", height=80)
        submitted = st.form_submit_button("Add Player", type="primary")

    if submitted:
        if not name.strip():
            st.error("Name is required.")
            return
        db.upsert_player(
            name=name.strip(),
            preferred_squad=preferred_squad or None,
            batting_rating=batting,
            bowling_rating=bowling,
            fielding_rating=fielding,
            bowling_type=bowling_type,
            preferred_batting_position=bat_pos,
            tier=tier,
            primary_strength=primary_strength,
            notes=notes,
        )
        st.success(f"Added {name.strip()}")
        st.rerun()


@st.dialog("Edit Player", width="large")
def _edit_player_dialog(player_id: int):
    player = db.get_player(player_id)
    if not player:
        st.error("Player not found.")
        return

    sq_val = player.get("preferred_squad") or ""
    sq_idx = SQUADS.index(sq_val) if sq_val in SQUADS else 0
    bt_val = player.get("bowling_type") or "None"
    bt_idx = BOWLING_TYPES.index(bt_val) if bt_val in BOWLING_TYPES else 0
    bp_val = player.get("preferred_batting_position") or "Middle"
    bp_idx = BAT_POSITIONS.index(bp_val) if bp_val in BAT_POSITIONS else 1
    tier_val = player.get("tier") or "Medium"
    tier_idx = TIERS.index(tier_val) if tier_val in TIERS else 1
    ps_val = player.get("primary_strength") or "All-rounder"
    ps_idx = PRIMARY_STRENGTHS.index(ps_val) if ps_val in PRIMARY_STRENGTHS else 0

    with st.form("edit_player_form"):
        name = st.text_input("Name *", value=player["name"])
        preferred_squad = st.selectbox(
            "Preferred Squad", SQUADS, index=sq_idx,
            format_func=lambda x: "No preference" if x == "" else x,
        )
        c1, c2 = st.columns(2)
        tier = c1.selectbox("Player Tier", TIERS, index=tier_idx)
        primary_strength = c2.selectbox("Primary Strength", PRIMARY_STRENGTHS, index=ps_idx)
        c3, c4, c5 = st.columns(3)
        batting = c3.slider("Batting Rating", 1, 10, int(player["batting_rating"] or 5))
        bowling = c4.slider("Bowling Rating", 1, 10, int(player["bowling_rating"] or 5))
        fielding = c5.slider("Fielding Rating", 1, 10, int(player["fielding_rating"] or 5))
        bowling_type = st.selectbox("Bowling Type", BOWLING_TYPES, index=bt_idx)
        bat_pos = st.selectbox("Batting Position", BAT_POSITIONS, index=bp_idx)
        notes = st.text_area("Notes", value=player.get("notes") or "", height=80)
        submitted = st.form_submit_button("Save Changes", type="primary")

    if submitted:
        if not name.strip():
            st.error("Name is required.")
            return
        db.upsert_player(
            name=name.strip(),
            preferred_squad=preferred_squad or None,
            batting_rating=batting,
            bowling_rating=bowling,
            fielding_rating=fielding,
            bowling_type=bowling_type,
            preferred_batting_position=bat_pos,
            tier=tier,
            primary_strength=primary_strength,
            notes=notes,
            player_id=player_id,
        )
        st.success("Saved!")
        st.rerun()


@st.dialog("Confirm Delete", width="small")
def _confirm_delete_player_dialog(player_id: int, player_name: str):
    st.warning(f"Delete **{player_name}**? This also removes their game history.")
    c1, c2 = st.columns(2)
    if c1.button("Yes, Delete", type="primary", use_container_width=True):
        db.delete_player(player_id)
        st.rerun()
    if c2.button("Cancel", use_container_width=True):
        st.rerun()


def render():
    st.header("Players")

    _, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("+ Add Player", type="primary", use_container_width=True):
            _add_player_dialog()

    stats = db.get_player_stats()

    if not stats:
        st.info("No players yet. Add one above or import a CSV from the sidebar.")
        return

    squad_filter = st.selectbox(
        "Filter by Squad",
        ["All", "U11 Sunday", "U11 Tuesday", "U12", "No Squad Assigned"],
        label_visibility="collapsed",
    )

    filtered = stats
    if squad_filter == "No Squad Assigned":
        filtered = [p for p in stats if not p["preferred_squad"]]
    elif squad_filter != "All":
        filtered = [p for p in stats if p["preferred_squad"] == squad_filter]

    st.caption(f"Showing {len(filtered)} of {len(stats)} players")

    _render_player_cards(filtered)

    st.divider()
    st.subheader("Edit / Delete Player")

    player_names = [p["name"] for p in filtered]
    selected = st.selectbox("Select player", ["—"] + player_names, label_visibility="collapsed")

    if selected != "—":
        player = next(p for p in filtered if p["name"] == selected)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Edit Player", type="primary", use_container_width=True):
                _edit_player_dialog(player["id"])
        with c2:
            if st.button("Delete Player", use_container_width=True):
                _confirm_delete_player_dialog(player["id"], player["name"])

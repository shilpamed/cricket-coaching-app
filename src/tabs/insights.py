import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import db

SQUAD_COLORS = {
    "U11 Sunday": "#2980b9",
    "U11 Tuesday": "#27ae60",
    "U12": "#e67e22",
}


def render():
    st.header("Insights")

    stats = db.get_player_stats()
    games = db.get_games()

    if not stats and not games:
        st.info("No data yet. Import your CSV from the sidebar to see insights.")
        return

    # ── Row 1: Results + Appearances ─────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Match Results")
        wld = db.get_win_loss_stats()
        total_results = sum(wld.values())
        if total_results == 0:
            games_count = len(games)
            st.info(
                f"{games_count} game(s) recorded but no results logged yet. "
                "Add results via the Games tab."
            )
        else:
            fig = go.Figure(go.Pie(
                labels=["Won", "Lost", "Draw"],
                values=[wld["W"], wld["L"], wld["D"]],
                hole=0.45,
                marker_colors=["#2ecc71", "#e74c3c", "#95a5a6"],
                textinfo="label+percent",
            ))
            fig.update_layout(
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 Won", wld["W"])
            c2.metric("🔴 Lost", wld["L"])
            c3.metric("⚪ Draw", wld["D"])

    with col2:
        st.subheader("Player Appearances")
        active = [p for p in stats if p["games_played"] > 0]
        if not active:
            st.info("No games played yet.")
        else:
            fig = go.Figure(go.Pie(
                labels=[p["name"] for p in active],
                values=[p["games_played"] for p in active],
                textinfo="none",
            ))
            fig.update_layout(
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(font=dict(size=9), orientation="v"),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Row 2: Fairness bar chart ─────────────────────────────────────────────
    st.subheader("Playing Time Fairness")

    active_all = [p for p in stats if p["games_played"] + p["games_invited"] > 0]
    if active_all:
        sorted_players = sorted(active_all, key=lambda x: x["games_played"])
        names = [p["name"] for p in sorted_players]
        played_vals = [p["games_played"] for p in sorted_players]
        invited_vals = [p["games_invited"] for p in sorted_players]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Played", x=names, y=played_vals,
            marker_color="#3498db",
        ))
        fig.add_trace(go.Bar(
            name="Invited (not played)", x=names, y=invited_vals,
            marker_color="#f39c12",
        ))
        fig.update_layout(
            barmode="stack",
            height=380,
            margin=dict(t=10, b=80, l=10, r=10),
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data yet.")

    st.divider()

    # ── Row 3: Not played recently ────────────────────────────────────────────
    st.subheader("Players Not Played Recently")
    days_threshold = st.slider("Show players not played in the last X days", 7, 90, 21)

    not_recent = [
        p for p in stats
        if p["days_since_last_game"] is None or p["days_since_last_game"] >= days_threshold
    ]

    if not_recent:
        sorted_players = sorted(
            not_recent,
            key=lambda p: p["days_since_last_game"] if p["days_since_last_game"] is not None else 9999,
            reverse=True,
        )
        rows_html = ""
        for p in sorted_players:
            squad = p.get("preferred_squad") or None
            sc = SQUAD_COLORS.get(squad or "", "#95a5a6")
            squad_label = squad or "—"
            days = p["days_since_last_game"]
            days_str = str(days) if days is not None else "Never"
            urgency = "#e74c3c" if days is None or days >= 30 else "#e67e22"
            rows_html += f"""
<tr>
  <td style="padding:8px 10px;font-weight:500;">{p["name"]}</td>
  <td style="padding:8px 10px;">
    <span style="background:{sc};color:white;padding:2px 8px;border-radius:10px;font-size:11px;">{squad_label}</span>
  </td>
  <td style="padding:8px 10px;text-align:center;">{p["games_played"]}</td>
  <td style="padding:8px 10px;text-align:center;">{p["games_invited"]}</td>
  <td style="padding:8px 10px;">{p["last_game_date"] or "Never"}</td>
  <td style="padding:8px 10px;text-align:center;">
    <span style="color:{urgency};font-weight:600;">{days_str}</span>
  </td>
</tr>"""
        st.markdown(
            f"""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:13px;
    background:white;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.07);">
  <thead>
    <tr style="background:#1e7a1e;color:white;">
      <th style="padding:10px 10px;text-align:left;">Name</th>
      <th style="padding:10px 10px;text-align:left;">Squad</th>
      <th style="padding:10px 10px;text-align:center;">Played</th>
      <th style="padding:10px 10px;text-align:center;">Invited</th>
      <th style="padding:10px 10px;text-align:left;">Last Played</th>
      <th style="padding:10px 10px;text-align:center;">Days Since</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.success(f"All players have played within the last {days_threshold} days.")

    st.divider()

    # ── Row 4: Games by squad ─────────────────────────────────────────────────
    st.subheader("Games by Squad")
    if games:
        squad_counts: dict[str, int] = {}
        for g in games:
            sq = g.get("squad") or "Unknown"
            squad_counts[sq] = squad_counts.get(sq, 0) + 1

        c1, c2, c3 = st.columns(len(squad_counts) if squad_counts else 1)
        cols = [c1, c2, c3]
        for i, (sq, cnt) in enumerate(sorted(squad_counts.items())):
            cols[min(i, 2)].metric(sq, cnt)
    else:
        st.info("No games recorded yet.")

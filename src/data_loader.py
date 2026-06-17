import re
from datetime import datetime, date

import pandas as pd

from src import db


def parse_date_str(date_str: str) -> date:
    clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str.strip(), flags=re.IGNORECASE).strip()
    for fmt in ["%d %B %Y", "%d %b %Y"]:
        try:
            return datetime.strptime(f"{clean} 2026", fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def parse_match_type(match_type: str) -> tuple[str, str]:
    mt = match_type.strip()
    mt_lower = mt.lower()

    if "u12" in mt_lower:
        age_group = "U12"
    elif "u11" in mt_lower:
        age_group = "U11"
    else:
        age_group = "Other"

    if "north" in mt_lower:
        competition = "North"
    elif "south" in mt_lower:
        competition = "South"
    elif "friendly" in mt_lower:
        competition = "Friendly"
    elif "tournament" in mt_lower:
        competition = "Tournament"
    elif "pre season" in mt_lower or "preseason" in mt_lower:
        competition = "Pre-season"
    else:
        competition = "Other"

    return age_group, competition


def infer_squad(game_date: date, age_group: str) -> str:
    if age_group == "U12":
        return "U12"
    day = game_date.strftime("%A")
    if day == "Tuesday":
        return "U11 Tuesday"
    if day == "Sunday":
        return "U11 Sunday"
    return f"U11 {day}"


def import_cricket_csv(file_buffer) -> str:
    """
    Import the CricketTest.csv format.

    Row 0: preference labels (sparse) — "Sunday preferred", "Tuesday Preferred", etc.
    Row 1: column headers — blank, "Match", blank, player_name, player_name, ...
    Row 2: blank
    Rows 3+: game data rows
    Last rows: blank rows + totals row
    """
    try:
        df = pd.read_csv(
            file_buffer, header=None, dtype=str,
            keep_default_na=False, encoding="utf-8-sig",
        )
    except Exception:
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, header=None, dtype=str, keep_default_na=False)

    pref_row = df.iloc[0].tolist()
    header_row = df.iloc[1].tolist()

    # Extract players from col 3 onwards
    players: list[dict] = []
    for i in range(3, len(header_row)):
        name = str(header_row[i]).strip()
        if not name or name in ("nan", ""):
            continue
        raw_pref = str(pref_row[i]).strip() if i < len(pref_row) else ""
        raw_pref = raw_pref if raw_pref not in ("nan", "") else ""
        if "sunday" in raw_pref.lower():
            pref_squad = "U11 Sunday"
        elif "tuesday" in raw_pref.lower():
            pref_squad = "U11 Tuesday"
        else:
            pref_squad = None
        players.append({"col_idx": i, "name": name, "preferred_squad": pref_squad})

    for p in players:
        db.upsert_player(name=p["name"], preferred_squad=p["preferred_squad"])

    player_id_map = {p["name"]: p["id"] for p in db.get_players()}

    # Build set of existing games to avoid duplicates on re-import
    existing_games: dict[tuple, int] = {
        (g["date"], g["opponent"]): g["id"] for g in db.get_games()
    }

    games_imported = 0
    for row_idx in range(2, len(df)):
        row = df.iloc[row_idx].tolist()
        date_str = str(row[0]).strip()
        match_type = str(row[1]).strip() if len(row) > 1 else ""
        opponent = str(row[2]).strip() if len(row) > 2 else ""

        if not date_str or date_str in ("nan", ""):
            continue
        if "total" in date_str.lower() or "total" in match_type.lower():
            continue
        if not match_type or match_type in ("nan", ""):
            continue

        try:
            game_date = parse_date_str(date_str)
        except ValueError:
            continue

        age_group, competition = parse_match_type(match_type)
        squad = infer_squad(game_date, age_group)

        key = (str(game_date), opponent)
        if key in existing_games:
            game_id = existing_games[key]
        else:
            game_id = db.upsert_game(
                date_val=game_date,
                opponent=opponent,
                match_type=match_type,
                age_group=age_group,
                competition=competition,
                squad=squad,
            )
            existing_games[key] = game_id

        played_ids, invited_ids = [], []
        for p in players:
            val = str(row[p["col_idx"]]).strip() if p["col_idx"] < len(row) else ""
            pid = player_id_map.get(p["name"])
            if not pid:
                continue
            if val == "1":
                played_ids.append(pid)
            elif val == "0":
                invited_ids.append(pid)

        db.set_game_players(game_id, played_ids, invited_ids)
        games_imported += 1

    return f"Imported {len(players)} players and {games_imported} games successfully."


def import_players_csv(file_buffer) -> str:
    """Import a simple players CSV. Required column: name."""
    try:
        df = pd.read_csv(file_buffer, dtype=str, keep_default_na=False)
    except Exception as e:
        return f"Error reading CSV: {e}"

    df.columns = [c.strip().lower() for c in df.columns]
    if "name" not in df.columns:
        return "CSV must have a 'name' column."

    def _int(val, default):
        try:
            return max(1, min(10, int(val)))
        except (ValueError, TypeError):
            return default

    count = 0
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            continue
        db.upsert_player(
            name=name,
            preferred_squad=str(row.get("preferred_squad", "")).strip() or None,
            batting_rating=_int(row.get("batting_rating"), 5),
            bowling_rating=_int(row.get("bowling_rating"), 5),
            fielding_rating=_int(row.get("fielding_rating"), 5),
            bowling_type=str(row.get("bowling_type", "None")).strip() or "None",
            preferred_batting_position=str(row.get("preferred_batting_position", "Middle")).strip() or "Middle",
            notes=str(row.get("notes", "")).strip(),
        )
        count += 1
    return f"Imported {count} players."

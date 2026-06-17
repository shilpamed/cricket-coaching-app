import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "cricket.db"


def init_db():
    with _get_conn() as conn:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS players (

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                preferred_squad TEXT,
                batting_rating INTEGER DEFAULT 5,
                bowling_rating INTEGER DEFAULT 5,
                fielding_rating INTEGER DEFAULT 5,
                bowling_type TEXT DEFAULT 'None',
                preferred_batting_position TEXT DEFAULT 'Middle',
                tier TEXT DEFAULT 'Medium',
                primary_strength TEXT DEFAULT 'All-rounder',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                opponent TEXT NOT NULL,
                match_type TEXT NOT NULL,
                age_group TEXT NOT NULL,
                competition TEXT DEFAULT 'Other',
                squad TEXT,
                location TEXT DEFAULT '',
                opposition_strength TEXT DEFAULT 'Medium',
                result TEXT,
                our_score TEXT,
                opponent_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                status TEXT NOT NULL CHECK(status IN ('played', 'invited')),
                UNIQUE(game_id, player_id)
            );

            CREATE TABLE IF NOT EXISTS fixtures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                opponent TEXT NOT NULL,
                match_type TEXT NOT NULL,
                age_group TEXT NOT NULL,
                competition TEXT DEFAULT 'Other',
                squad TEXT,
                location TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        for migration in [
            "ALTER TABLE players ADD COLUMN tier TEXT DEFAULT 'Medium'",
            "ALTER TABLE players ADD COLUMN primary_strength TEXT DEFAULT 'All-rounder'",
            "ALTER TABLE games ADD COLUMN opposition_strength TEXT DEFAULT 'Medium'",
        ]:
            try:
                conn.execute(migration)
            except Exception:
                pass  # column already exists


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Players ───────────────────────────────────────────────────────────────────

def get_players() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM players ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def get_player(player_id: int) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
        return dict(row) if row else None


def upsert_player(
    name: str,
    preferred_squad: Optional[str] = None,
    batting_rating: int = 5,
    bowling_rating: int = 5,
    fielding_rating: int = 5,
    bowling_type: str = "None",
    preferred_batting_position: str = "Middle",
    tier: str = "Medium",
    primary_strength: str = "All-rounder",
    notes: str = "",
    player_id: Optional[int] = None,
) -> int:
    with _get_conn() as conn:
        if player_id:
            conn.execute(
                """UPDATE players SET name=?, preferred_squad=?, batting_rating=?,
                bowling_rating=?, fielding_rating=?, bowling_type=?,
                preferred_batting_position=?, tier=?, primary_strength=?, notes=?
                WHERE id=?""",
                (name, preferred_squad, batting_rating, bowling_rating, fielding_rating,
                 bowling_type, preferred_batting_position, tier, primary_strength, notes,
                 player_id),
            )
            return player_id
        cursor = conn.execute(
            """INSERT INTO players (name, preferred_squad, batting_rating, bowling_rating,
            fielding_rating, bowling_type, preferred_batting_position, tier, primary_strength, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                preferred_squad = COALESCE(excluded.preferred_squad, players.preferred_squad)""",
            (name, preferred_squad, batting_rating, bowling_rating, fielding_rating,
             bowling_type, preferred_batting_position, tier, primary_strength, notes),
        )
        return cursor.lastrowid


def delete_player(player_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM players WHERE id = ?", (player_id,))


# ── Games ─────────────────────────────────────────────────────────────────────

def get_games() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM games ORDER BY date DESC").fetchall()
        return [dict(r) for r in rows]


def get_game(game_id: int) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        return dict(row) if row else None


def upsert_game(
    date_val,
    opponent: str,
    match_type: str,
    age_group: str,
    competition: str = "Other",
    squad: Optional[str] = None,
    location: str = "",
    opposition_strength: str = "Medium",
    result: Optional[str] = None,
    our_score: Optional[str] = None,
    opponent_score: Optional[str] = None,
    game_id: Optional[int] = None,
) -> int:
    with _get_conn() as conn:
        if game_id:
            conn.execute(
                """UPDATE games SET date=?, opponent=?, match_type=?, age_group=?,
                competition=?, squad=?, location=?, opposition_strength=?,
                result=?, our_score=?, opponent_score=? WHERE id=?""",
                (str(date_val), opponent, match_type, age_group, competition, squad,
                 location, opposition_strength, result, our_score, opponent_score, game_id),
            )
            return game_id
        cursor = conn.execute(
            """INSERT INTO games (date, opponent, match_type, age_group, competition,
            squad, location, opposition_strength, result, our_score, opponent_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(date_val), opponent, match_type, age_group, competition, squad,
             location, opposition_strength, result, our_score, opponent_score),
        )
        return cursor.lastrowid


def delete_game(game_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM games WHERE id = ?", (game_id,))


# ── Game Players ──────────────────────────────────────────────────────────────

def get_game_players(game_id: int) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT gp.*, p.name as player_name
            FROM game_players gp JOIN players p ON gp.player_id = p.id
            WHERE gp.game_id = ? ORDER BY p.name""",
            (game_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def set_game_players(game_id: int, played_ids: list[int], invited_ids: list[int]):
    with _get_conn() as conn:
        conn.execute("DELETE FROM game_players WHERE game_id = ?", (game_id,))
        for pid in played_ids:
            conn.execute(
                "INSERT INTO game_players (game_id, player_id, status) VALUES (?, ?, 'played')",
                (game_id, pid),
            )
        for pid in invited_ids:
            conn.execute(
                "INSERT INTO game_players (game_id, player_id, status) VALUES (?, ?, 'invited')",
                (game_id, pid),
            )


def upsert_game_player(game_id: int, player_id: int, status: str):
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO game_players (game_id, player_id, status) VALUES (?, ?, ?)
            ON CONFLICT(game_id, player_id) DO UPDATE SET status = excluded.status""",
            (game_id, player_id, status),
        )


# ── Fixtures ──────────────────────────────────────────────────────────────────

def get_fixtures() -> list[dict]:
    """Return upcoming fixtures — games with a future date."""
    today = str(date.today())
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM games WHERE date >= ? ORDER BY date ASC", (today,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_fixture(fixture_id: int) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
        return dict(row) if row else None


def upsert_fixture(
    date_val,
    opponent: str,
    match_type: str,
    age_group: str,
    competition: str = "Other",
    squad: Optional[str] = None,
    location: str = "",
    fixture_id: Optional[int] = None,
) -> int:
    with _get_conn() as conn:
        if fixture_id:
            conn.execute(
                """UPDATE fixtures SET date=?, opponent=?, match_type=?, age_group=?,
                competition=?, squad=?, location=? WHERE id=?""",
                (str(date_val), opponent, match_type, age_group, competition, squad,
                 location, fixture_id),
            )
            return fixture_id
        cursor = conn.execute(
            """INSERT INTO fixtures (date, opponent, match_type, age_group, competition, squad, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(date_val), opponent, match_type, age_group, competition, squad, location),
        )
        return cursor.lastrowid


def delete_fixture(fixture_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM fixtures WHERE id = ?", (fixture_id,))


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_player_stats() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT
                p.id, p.name, p.preferred_squad,
                p.batting_rating, p.bowling_rating, p.fielding_rating,
                p.bowling_type, p.preferred_batting_position,
                p.tier, p.primary_strength, p.notes,
                COALESCE(SUM(CASE WHEN gp.status = 'played' THEN 1 ELSE 0 END), 0) AS games_played,
                COALESCE(SUM(CASE WHEN gp.status = 'invited' THEN 1 ELSE 0 END), 0) AS games_invited,
                MAX(CASE WHEN gp.status = 'played' THEN g.date END) AS last_game_date
            FROM players p
            LEFT JOIN game_players gp ON p.id = gp.player_id
            LEFT JOIN games g ON gp.game_id = g.id
            GROUP BY p.id
            ORDER BY p.name
        """).fetchall()

        today = date.today()
        result = []
        for r in rows:
            d = dict(r)
            if d["last_game_date"]:
                last = datetime.strptime(d["last_game_date"], "%Y-%m-%d").date()
                d["days_since_last_game"] = (today - last).days
            else:
                d["days_since_last_game"] = None
            result.append(d)
        return result


def get_win_loss_stats() -> dict:
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT result, COUNT(*) as count FROM games
            WHERE result IS NOT NULL AND result != ''
            GROUP BY result
        """).fetchall()
        stats = {"W": 0, "L": 0, "D": 0}
        for row in rows:
            if row["result"] in stats:
                stats[row["result"]] = row["count"]
        return stats

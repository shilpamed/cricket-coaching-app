# HH Cricket Coaching Dashboard

A Streamlit web app for managing junior cricket squads at Haywards Heath Cricket Club. Built to track players across multiple squads, record match history, and get AI-powered squad selection recommendations.

## Features

| Tab | What it does |
|-----|-------------|
| **Players** | View all players as cards with ratings, squad assignment, and game history. Add, edit, and delete players. |
| **Games** | Record past matches and upcoming fixtures. Track results, scores, and which players participated. |
| **Insights** | Win/loss charts, playing-time fairness bar chart, and a flag for players who haven't played recently. |
| **Squad Recommender** | AI-powered squad selection using Claude — picks the best 11 for an upcoming fixture based on player ratings, availability, and fairness. |

## Tech Stack

- **[Streamlit](https://streamlit.io/)** — UI framework
- **SQLite** — local persistent database (`cricket.db`, auto-created on first run)
- **[Plotly](https://plotly.com/python/)** — charts
- **[Anthropic Claude API](https://docs.anthropic.com/)** — AI squad recommendations
- **[uv](https://docs.astral.sh/uv/)** — Python package manager

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- An [Anthropic API key](https://console.anthropic.com/) (for the Squad Recommender tab)

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/hh-cricket-coaching.git
cd hh-cricket-coaching

# 2. Create your .env file
cp .env.example .env
# Edit .env and add your Anthropic API key

# 3. Run the app (uv handles the venv and dependencies automatically)
uv run streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Importing Historical Data

The sidebar has two importers:

**Games & Players CSV** — Use the format from `CricketTest.csv`:
- Columns: `Date`, `Match Type`, `Opponent`, then one column per player
- Player cell values: `1` = played, `0` = invited but couldn't play, blank = not involved

**Players-only CSV** — Minimum required column: `name`. Optional columns:

| Column | Values |
|--------|--------|
| `preferred_squad` | `U11 Sunday`, `U11 Tuesday`, `U12` |
| `batting_rating` | 1–10 |
| `bowling_rating` | 1–10 |
| `fielding_rating` | 1–10 |
| `bowling_type` | `Pace`, `Spin`, `None` |
| `preferred_batting_position` | `Top`, `Middle`, `Lower` |
| `tier` | `Strong`, `Medium`, `Developmental` |
| `notes` | free text |

A template CSV can be downloaded from the sidebar.

## Squad Logic

- Players belong to a **single pool** — there are no fixed squad rosters.
- Squad is recorded **per game**, not per player.
- Squad is auto-inferred from match date + type when importing CSVs:
  - U12 match type → `U12`
  - Tuesday date → `U11 Tuesday`
  - Sunday date → `U11 Sunday`

## Project Structure

```
.
├── app.py                  # Entry point — page config, CSS theme, sidebar, tabs
├── src/
│   ├── db.py               # All database access (SQLite via sqlite3)
│   ├── data_loader.py      # CSV import logic
│   ├── tabs/
│   │   ├── players.py      # Players tab
│   │   ├── games.py        # Games & Fixtures tab
│   │   ├── insights.py     # Insights & charts tab
│   │   └── squad_recommender.py  # AI squad selection tab
│   └── ai/
│       └── recommender.py  # Claude API integration
├── .env.example            # Environment variable template
├── pyproject.toml          # Dependencies
└── CricketTest.csv         # Sample historical data (2026 season, 33 players, 25 games)
```

## Development

```bash
# Install dependencies into the venv
uv sync

# Run with auto-reload
uv run streamlit run app.py
```

No test suite yet — the app is a single-user local tool.

## License

MIT

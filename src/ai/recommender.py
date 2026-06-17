import os

import anthropic


def generate_squad(
    fixture: dict,
    player_stats: list[dict],
    recent_games: list[dict],
    coach_notes: str = "",
) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = _build_prompt(fixture, player_stats, recent_games, coach_notes)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _build_prompt(
    fixture: dict,
    player_stats: list[dict],
    recent_games: list[dict],
    coach_notes: str,
) -> str:
    header = (
        "| Name | Squad | Tier | Strength | Batting | Bowling | Fielding "
        "| Bowl Type | Bat Pos | Played | Invited | Days Since Last |"
    )
    sep = "|------|-------|------|----------|---------|---------|---------|-----------|---------|--------|---------|----------------|"
    rows = [header, sep]
    for p in sorted(player_stats, key=lambda x: x["games_played"]):
        days = p["days_since_last_game"]
        days_str = f"{days}d ago" if days is not None else "Never played"
        rows.append(
            f"| {p['name']} "
            f"| {p.get('preferred_squad') or 'N/A'} "
            f"| {p.get('tier') or 'Medium'} "
            f"| {p.get('primary_strength') or 'All-rounder'} "
            f"| {p['batting_rating']}/10 "
            f"| {p['bowling_rating']}/10 "
            f"| {p['fielding_rating']}/10 "
            f"| {p.get('bowling_type') or 'N/A'} "
            f"| {p.get('preferred_batting_position') or 'N/A'} "
            f"| {p['games_played']} "
            f"| {p['games_invited']} "
            f"| {days_str} |"
        )
    player_table = "\n".join(rows)

    if recent_games:
        recent_lines = []
        for g in recent_games:
            result = g.get("result") or "No result recorded"
            score = ""
            if g.get("our_score") and g.get("opponent_score"):
                score = f" ({g['our_score']} – {g['opponent_score']})"
            opp_str = g.get("opposition_strength") or "Medium"
            recent_lines.append(
                f"- {g['date']}: vs {g['opponent']} "
                f"({g['match_type']}, {g.get('squad') or '?'}, {opp_str} opposition): {result}{score}"
            )
        recent_str = "\n".join(recent_lines)
    else:
        recent_str = "No recent games recorded."

    opposition_strength = fixture.get("opposition_strength") or "Medium"

    composition_guide = {
        "Strong": "5–6 Strong, 2–3 Medium, 2 Developmental (target minimum — see fairness rules below)",
        "Medium": "3–4 Strong, 4–5 Medium, 2–3 Developmental",
        "Weak":   "2–3 Strong, 3–4 Medium, 4–5 Developmental (prioritise development opportunity)",
    }
    target_composition = composition_guide.get(opposition_strength, composition_guide["Medium"])

    notes_section = f"## Coach Notes\n{coach_notes.strip()}" if coach_notes.strip() else "## Coach Notes\nNone provided."

    return f"""You are an expert youth cricket coach assistant helping a coach at Haywards Heath Cricket Club select a squad.

## Upcoming Match
- **Date**: {fixture['date']}
- **Opponent**: {fixture['opponent']}
- **Opposition Strength**: {opposition_strength}
- **Match Type**: {fixture['match_type']}
- **Age Group**: {fixture.get('age_group', 'Unknown')}
- **Squad**: {fixture.get('squad') or 'TBD'}
- **Location**: {fixture.get('location') or 'TBD'}

## Available Players

{player_table}

## Last 5 Games
{recent_str}

{notes_section}

## Selection Guidelines

Select exactly 11 players using the following priorities in order:

### 1. Fairness (non-negotiable baseline)
A child who was invited multiple times and never played must be prioritised — this is youth cricket and every child deserves game time. Track the invited-but-not-played count carefully.

### 2. Opposition-Adjusted Composition
The opposition is rated **{opposition_strength}**. Target squad composition: **{target_composition}**.

The 2 Developmental minimum for Strong opposition is a strong default — you may deviate below it only if truly unavoidable (e.g. not enough Developmental players available, or a Developmental player was given chances in the last 2 games). **If you do go below 2 Developmental players, you must explicitly explain why in the Fairness Notes.**

### 3. Team Balance
Include a mix of batters, bowlers, and all-rounders. Aim for at least 2–3 genuine bowlers. Use Primary Strength and Bowl Type to inform the batting order and bowling attack.

### 4. Coach Notes Override
If Coach Notes are provided, treat them as high-priority context that can override the above guidance. Reason explicitly about how you are applying them.

## Response Format

### Selected XI
List all 11 players with their suggested batting position number (1–11), their tier, and a one-sentence reason for selection.

### Bowling Attack
List your suggested bowlers in bowling order with their bowling type.

### Fairness Notes
Highlight players who are overdue a game or have a high invited-but-not-played count. If you deviated from the Developmental minimum, explain clearly here.

### Notable Omissions
Mention 1–3 players who narrowly missed out and briefly why.

Keep each reason concise (one sentence). Be practical and specific — this coach needs actionable advice."""

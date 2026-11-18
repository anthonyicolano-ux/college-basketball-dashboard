"""Validate private full-coverage basketball JSON before KV publication.

No API requests, credentials, provider records, or KV writes occur here.
Usage: python private-site/validate_full_coverage.py teams.json players.json
"""
import json
import math
from datetime import datetime
import sys
from pathlib import Path

SEASON = 2027
MAX_TEAMS = 400
MAX_PLAYERS = 10000
TEAM_NUMBERS = ("wins", "losses", "games", "ppg", "oppPpg", "offRating", "defRating", "netRating", "scoringMargin")
PLAYER_NUMBERS = ("games", "points", "rebounds", "assists", "minutes")


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Dataset must be an object")
    if data.get("schemaVersion") != 1 or data.get("season") != SEASON or data.get("demo") is not False:
        raise ValueError("Expected real 2026-27 schemaVersion 1 dataset")
    if data.get("approvedForPrivateDisplay") is not True:
        raise ValueError("Explicit private-display approval required")
    if not isinstance(data.get("source"), str) or not data["source"].strip():
        raise ValueError("Source provenance required")
    if not isinstance(data.get("generatedAt"), str) or not data["generatedAt"].strip():
        raise ValueError("Generation timestamp required")
    try:
        datetime.fromisoformat(data["generatedAt"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid generation timestamp") from exc
    if not isinstance(data.get("scope"), str) or not data["scope"].strip():
        raise ValueError("Dataset scope required")
    if not isinstance(data.get("rows"), list):
        raise ValueError("Rows must be an array")
    return data


def number(row, field):
    value = row.get(field)
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_teams(data):
    rows = data["rows"]
    if not 2 <= len(rows) <= MAX_TEAMS:
        raise ValueError("Team count outside supported bounds")
    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Team row {i} must be an object")
        name = row.get("team")
        if not isinstance(name, str) or not name.strip() or len(name) > 120 or name in seen:
            raise ValueError(f"Invalid or duplicate team in row {i}")
        seen.add(name)
        if not isinstance(row.get("conference"), str) or not row["conference"].strip():
            raise ValueError(f"Missing conference for {name}")
        if any(not number(row, field) for field in TEAM_NUMBERS):
            raise ValueError(f"Missing or nonfinite required team metrics for {name}")
        if any(row[field] < 0 for field in ("wins", "losses", "games")):
            raise ValueError(f"Negative game counts for {name}")
        if any(int(row[field]) != row[field] for field in ("wins", "losses", "games")):
            raise ValueError(f"Noninteger game counts for {name}")
        if row["wins"] + row["losses"] != row["games"]:
            raise ValueError(f"Unreconciled W-L-GP for {name}")
    return seen


def validate_players(data, teams):
    rows = data["rows"]
    if not 1 <= len(rows) <= MAX_PLAYERS:
        raise ValueError("Player count outside supported bounds")
    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Player row {i} must be an object")
        name, team = row.get("name"), row.get("team")
        if not isinstance(name, str) or not name.strip() or len(name) > 150:
            raise ValueError(f"Invalid player name in row {i}")
        if not isinstance(team, str) or not team.strip() or team not in teams:
            raise ValueError(f"Player team outside covered teams: {team}")
        if any(not number(row, field) for field in PLAYER_NUMBERS):
            raise ValueError(f"Missing or nonfinite player metrics for {name}")
        if row["games"] < 0 or int(row["games"]) != row["games"]:
            raise ValueError(f"Invalid games for {name}")
        # A stable provider player ID is preferred; names may legitimately repeat.
        identity = row.get("id")
        if identity is not None:
            key = (team, str(identity))
            if key in seen:
                raise ValueError(f"Duplicate provider player ID for {team}")
            seen.add(key)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: validate_full_coverage.py teams.json players.json")
    teams = load(sys.argv[1])
    players = load(sys.argv[2])
    names = validate_teams(teams)
    validate_players(players, names)
    print(f"VALID: {len(names)} teams and {len(players['rows'])} players; no data published")


if __name__ == "__main__":
    main()

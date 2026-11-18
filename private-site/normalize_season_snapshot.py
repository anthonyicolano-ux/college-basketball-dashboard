"""Offline normalization of season snapshots into private dashboard datasets.

No network, no secrets, no KV writes. Rejects unknown provider schemas rather than
fabricating stats. Raw snapshots are never committed or printed.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from validate_full_coverage import validate_teams, validate_players

TEAM_FIELDS = ("team", "conference", "games", "wins", "losses", "ppg",
               "oppPpg", "offRating", "defRating", "netRating", "scoringMargin")
PLAYER_FIELDS = ("name", "team", "games", "points", "rebounds", "assists", "minutes")


def normalize_rows(raw, fields, kind):
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{kind}: expected nonempty season-wide list")
    normalized = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{kind}: row {i} must be an object")
        missing = [field for field in fields if field not in item]
        if missing:
            raise ValueError(f"{kind}: provider schema mapping required for {', '.join(missing)}")
        normalized.append(dict(item))
    return normalized


def build(raw_teams, raw_players, *, display_permission_confirmed=False,\n          expected_team_count=None):
    if display_permission_confirmed is not True:
        raise ValueError("Private-display permission must be explicitly confirmed")
    team_rows = normalize_rows(raw_teams, TEAM_FIELDS, "teams")\n    if expected_team_count is None or type(expected_team_count) is not int or expected_team_count < 300:\n        raise ValueError("Verified Division I team count of at least 300 is required")\n    if len(team_rows) != expected_team_count:\n        raise ValueError("Incomplete team coverage; refusing to label snapshot full coverage")
    player_rows = normalize_rows(raw_players, PLAYER_FIELDS, "players")
    timestamp = datetime.now(timezone.utc).isoformat()
    meta = dict(schemaVersion=1, season=2027, seasonLabel="2026-27",
                generatedAt=timestamp, demo=False, source="CollegeBasketballData.com",
                approvedForPrivateDisplay=True, scope="Private season-wide statistics")
    teams = {**meta, "rows": team_rows}
    players = {**meta, "rows": player_rows}
    names = validate_teams(teams)
    validate_players(players, names)
    return teams, players


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_teams", type=Path)
    parser.add_argument("raw_players", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--confirm-display-permission", action="store_true")\n    parser.add_argument("--expected-team-count", type=int, required=True)
    args = parser.parse_args()
    raw_teams = json.loads(args.raw_teams.read_text(encoding="utf-8"))
    raw_players = json.loads(args.raw_players.read_text(encoding="utf-8"))
    teams, players = build(raw_teams, raw_players,
                           display_permission_confirmed=args.confirm_display_permission,\n                           expected_team_count=args.expected_team_count)
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("Output directory must be empty")
    args.out.mkdir(parents=True, exist_ok=True)
    for filename, data in (("teams.json", teams), ("players.json", players)):
        (args.out / filename).write_text(json.dumps(data), encoding="utf-8")
    print("Validated private datasets written; no KV publication")


if __name__ == "__main__":
    main()

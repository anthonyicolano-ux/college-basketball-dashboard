"""Offline end-to-end preparation gate for a future real 2027 release.

Requires a separately reviewed season-specific Division I membership file.
No network, KV writes, or raw-record printing. Never commit raw input files.
"""
import argparse
import json
from pathlib import Path
from filter_division_one import filter_division_one, load_approved_ids
from verified_2027_provider_mapping import map_team, map_player
from normalize_season_snapshot import build


def prepare(raw_teams, raw_players, approved_ids):
    teams, players = filter_division_one(raw_teams, raw_players, approved_ids)
    mapped_teams = [map_team(team) for team in teams]
    mapped_players = [map_player(player) for player in players]
    return build(mapped_teams, mapped_players,
                 display_permission_confirmed=True,
                 expected_team_count=len(approved_ids))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_teams", type=Path)
    parser.add_argument("raw_players", type=Path)
    parser.add_argument("--reviewed-membership", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--confirm-display-permission", action="store_true")
    args = parser.parse_args()
    if not args.confirm_display_permission:
        parser.error("Explicit private-display permission required")
    ids = load_approved_ids(args.reviewed_membership)
    teams, players = prepare(
        json.loads(args.raw_teams.read_text(encoding="utf-8")),
        json.loads(args.raw_players.read_text(encoding="utf-8")), ids)
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("Output directory must be empty")
    args.out.mkdir(parents=True, exist_ok=True)
    for filename, data in (("teams.json", teams), ("players.json", players)):
        (args.out / filename).write_text(json.dumps(data), encoding="utf-8")
    print(f"Validated private release prepared: {len(teams['rows'])} teams, {len(players['rows'])} players; no publication")


if __name__ == "__main__":
    main()

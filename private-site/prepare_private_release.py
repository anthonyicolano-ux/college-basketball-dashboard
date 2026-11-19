"""Offline publication manifest for validated private dashboard data.

This prepares an immutable release plan, not a KV write. Never commit generated
payloads: they contain licensed provider-derived records.
"""
import hashlib
import json
from validate_full_coverage import load, validate_teams, validate_players


def release_manifest(teams_path, players_path):
    teams = load(teams_path)
    players = load(players_path)
    team_names = validate_teams(teams)
    if len(team_names) < 300:
        raise ValueError("Refusing to publish partial team coverage")
    validate_players(players, team_names)
    if teams["generatedAt"] != players["generatedAt"]:
        raise ValueError("Team and player snapshots must share one generation timestamp")
    if teams["source"] != players["source"]:
        raise ValueError("Source mismatch between team and player snapshots")
    if len(players["rows"]) <= 203:
        raise ValueError("Refusing to publish pilot-sized player coverage")
    result = {"season": 2027, "generatedAt": teams["generatedAt"],
              "teamCount": len(team_names), "playerCount": len(players["rows"]),
              "keys": {}}
    for key, path in (("teams", teams_path), ("players", players_path)):
        raw = path.read_bytes()
        result["keys"][key] = {"sha256": hashlib.sha256(raw).hexdigest(),
                               "bytes": len(raw)}
    return result


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("teams", type=Path)
    parser.add_argument("players", type=Path)
    args = parser.parse_args()
    print(json.dumps(release_manifest(args.teams, args.players), indent=2))


if __name__ == "__main__":
    main()

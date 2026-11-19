"""Offline, value-free audit of provider fields needed by the 2027 mapper.

Checks *all* records, not just path names. No API calls, raw data printing,
publication, or inferred NCAA Division I membership.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from verified_2027_provider_mapping import TEAM_PATHS, PLAYER_PATHS, at


def inspect(rows, paths):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty provider list required")
    missing = Counter()
    wrong_types = Counter()
    zero_games = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Provider rows must be objects")
        for label, path in paths.items():
            try:
                value = at(row, path)
            except ValueError:
                missing[label] += 1
                continue
            if label in ("team", "conference", "name") and not isinstance(value, str):
                wrong_types[label] += 1
            elif label not in ("team", "conference", "name") and (isinstance(value, bool) or not isinstance(value, (int, float, str))):
                wrong_types[label] += 1
        if row.get("games") == 0:
            zero_games += 1
    return {"records": len(rows), "missingByField": dict(sorted(missing.items())),
            "wrongTypeByField": dict(sorted(wrong_types.items())),
            "zeroGameRecords": zero_games}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_teams", type=Path)
    parser.add_argument("raw_players", type=Path)
    args = parser.parse_args()
    report = {
        "teams": inspect(json.loads(args.raw_teams.read_text()), TEAM_PATHS),
        "players": inspect(json.loads(args.raw_players.read_text()), PLAYER_PATHS),
    }
    print(json.dumps(report, indent=2))
    if any(group["missingByField"] or group["wrongTypeByField"] for group in report.values()):
        raise SystemExit("Mapped fields incomplete; do not publish")


if __name__ == "__main__":
    main()

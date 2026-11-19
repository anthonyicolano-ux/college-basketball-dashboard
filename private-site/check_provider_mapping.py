"""Offline provider schema compatibility report; prints field names only, never records.

Usage: python private-site/check_provider_mapping.py raw-teams.json raw-players.json
No API requests, publication, or credentials. This is a schema review tool,
not evidence of data-use permission or full Division I coverage.
"""
import json
import sys
from pathlib import Path
from normalize_season_snapshot import TEAM_FIELDS, PLAYER_FIELDS


def summarize(rows, required):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected a nonempty array of season records")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Every season record must be an object")
    keys = set().union(*(set(row) for row in rows))
    missing_counts = {field: sum(field not in row for row in rows) for field in required}
    return {
        "recordCount": len(rows),
        "availableFieldNames": sorted(keys),
        "missingRequiredFields": {key: count for key, count in missing_counts.items() if count},
        "mappingReady": not any(missing_counts.values()),
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: check_provider_mapping.py raw-teams.json raw-players.json")
    result = {}
    for kind, filename, fields in (
        ("teams", sys.argv[1], TEAM_FIELDS),
        ("players", sys.argv[2], PLAYER_FIELDS),
    ):
        rows = json.loads(Path(filename).read_text(encoding="utf-8"))
        result[kind] = summarize(rows, fields)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

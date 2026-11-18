"""Print only schema metadata for private basketball JSON (no player records).

Usage: python private-site/inspect_private_schema.py path/to/players.json
Do not upload the JSON file or paste private player rows into an issue.
"""
import json
import sys
from pathlib import Path


def summarize(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    rows = data.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Expected rows array")
    keys = sorted(set().union(*(row.keys() for row in rows if isinstance(row, dict))))
    types = {}
    for key in keys:
        types[key] = sorted({type(row.get(key)).__name__ for row in rows if isinstance(row, dict)})
    required_player_fields = {"name", "team", "games", "points", "rebounds", "assists", "minutes"}
    required_team_fields = {"team", "conference", "wins", "losses", "games", "ppg",
                            "oppPpg", "offRating", "defRating", "netRating", "scoringMargin"}
    is_player = "name" in keys
    expected = required_player_fields if is_player else required_team_fields
    required_types_ok = all(
        key in types and all(kind in {"int", "float"} for kind in types[key])
        for key in ({"games", "points", "rebounds", "assists", "minutes"}
                    if is_player else {"wins", "losses", "games", "ppg", "oppPpg",
                                       "offRating", "defRating", "netRating", "scoringMargin"})
    )
    return {
        "schemaVersion": data.get("schemaVersion"),
        "season": data.get("season"),
        "demo": data.get("demo"),
        "approvedForPrivateDisplay": data.get("approvedForPrivateDisplay"),
        "hasSource": isinstance(data.get("source"), str) and bool(data["source"].strip()),
        "hasScope": isinstance(data.get("scope"), str) and bool(data["scope"].strip()),
        "hasGeneratedAt": isinstance(data.get("generatedAt"), str) and bool(data["generatedAt"].strip()),
        "rowCount": len(rows),
        "fields": keys,
        "fieldTypes": types,
        "missingRequiredFields": sorted(expected - set(keys)),
        "requiredNumericTypesValid": required_types_ok,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: inspect_private_schema.py private-players.json")
    print(json.dumps(summarize(sys.argv[1]), indent=2))

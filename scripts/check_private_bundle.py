"""Validate an approved private basketball data bundle without publishing it.

Usage:
 python scripts/check_private_bundle.py /secure/path/to/bundle

This script reads files only; it never copies, uploads, or prints player records.
The approval flag is an operator assertion, not proof of licensing rights.
"""
import json
import sys
from pathlib import Path

SEASON = 2027
FILES = ("teams.json", "players.json")


def check_bundle(folder):
    folder = Path(folder)
    result = {}
    for filename in FILES:
        path = folder / filename
        if not path.is_file():
            raise ValueError(f"{filename}: missing")
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schemaVersion") != 1 or doc.get("season") != SEASON:
            raise ValueError(f"{filename}: invalid schema or season")
        if doc.get("demo") is not False:
            raise ValueError(f"{filename}: not a real dataset")
        if doc.get("approvedForPrivateDisplay") is not True:
            raise ValueError(f"{filename}: private-display approval missing")
        for key in ("generatedAt", "scope", "source"):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                raise ValueError(f"{filename}: {key} missing")
        rows = doc.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{filename}: no records")
        identity = "team" if filename == "teams.json" else "name"
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or not isinstance(row.get(identity), str) or not row[identity].strip():
                raise ValueError(f"{filename}: invalid record identity at index {i}")
            if not isinstance(row.get("games"), int) or isinstance(row.get("games"), bool) or row["games"] < 0:
                raise ValueError(f"{filename}: invalid games at index {i}")
            if filename == "players.json" and (not isinstance(row.get("team"), str) or not row["team"].strip()):
                raise ValueError(f"{filename}: missing player team at index {i}")
            if filename == "teams.json":
                w, l = row.get("wins"), row.get("losses")
                if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in (w, l)) or w + l != row["games"]:
                    raise ValueError(f"{filename}: unresolved team record at index {i}")
        result[filename] = len(rows)
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/check_private_bundle.py /secure/path/to/bundle")
    try:
        counts = check_bundle(sys.argv[1])
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Private bundle rejected: {exc}")
    print("Private bundle validated locally; no data uploaded or published.")
    print("Counts: " + ", ".join(f"{name}: {count}" for name, count in counts.items()))
    print("Licensing and private-hosting authorization must be verified separately.")

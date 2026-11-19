"""Offline nested provider schema inventory with no raw record values.

Inspect existing private snapshots before deciding which fields can be mapped.
Never calls provider APIs, publishes datasets, or prints player information.
"""
import json
from collections import Counter
from pathlib import Path


def flatten_paths(record, prefix=""):
    if not isinstance(record, dict):
        return []
    paths = []
    for key, value in record.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            paths.extend(flatten_paths(value, name))
        else:
            paths.append(name)
    return paths


def inventory(rows):
    if not isinstance(rows, list) or not rows or any(not isinstance(x, dict) for x in rows):
        raise ValueError("Expected nonempty list of provider objects")
    counts = Counter()
    for row in rows:
        counts.update(set(flatten_paths(row)))
    return {"recordCount": len(rows),
            "paths": [{"path": key, "present": counts[key],
                       "missing": len(rows)-counts[key]}
                      for key in sorted(counts)]}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("teams", type=Path)
    parser.add_argument("players", type=Path)
    args = parser.parse_args()
    result = {}
    for kind, path in (("teams", args.teams), ("players", args.players)):
        result[kind] = inventory(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

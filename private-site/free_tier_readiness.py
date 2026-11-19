"""Offline free-tier readiness check for season-wide basketball snapshots.

This deliberately does not require paid advanced efficiency metrics.
It makes no API requests, KV writes, or claims of full coverage.
"""
import math

TEAM_BASIC = ("team", "games", "wins", "losses", "ppg", "oppPpg")
PLAYER_BASIC = ("name", "team", "games", "points", "rebounds", "assists", "minutes")


def inspect(rows, fields):
    if not isinstance(rows, list) or not rows:
        raise ValueError("Expected nonempty records")
    missing = {field: 0 for field in fields}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each record must be an object")
        for field in fields:
            value = row.get(field)
            if value is None or isinstance(value, bool) or (
                isinstance(value, float) and not math.isfinite(value)
            ) or (isinstance(value, str) and not value.strip()):
                missing[field] += 1
    return {"records": len(rows), "missing": {k: v for k, v in missing.items() if v},
            "basicReady": not any(missing.values())}


def inspect_snapshot(teams, players):
    return {"teams": inspect(teams, TEAM_BASIC),
            "players": inspect(players, PLAYER_BASIC)}

"""Fail-closed Division I membership filtering for CBBD season snapshots.

The season endpoints contain non-DI programs. Membership must come from a
separately reviewed, season-specific Division I team ID list, never a guessed
conference or the total number of provider records. No network or publication.
"""
import json
from pathlib import Path


def filter_division_one(teams, players, approved_team_ids):
    if not isinstance(teams, list) or not isinstance(players, list):
        raise ValueError("Expected team and player lists")
    if not isinstance(approved_team_ids, (list, set, tuple)):
        raise ValueError("Reviewed Division I team ID list required")
    ids = set()
    for item in approved_team_ids:
        if isinstance(item, bool) or not isinstance(item, (int, str)) or not str(item).strip():
            raise ValueError("Invalid approved team ID")
        key = str(item)
        if key in ids:
            raise ValueError("Duplicate approved team ID")
        ids.add(key)
    if len(ids) < 300 or len(ids) > 400:
        raise ValueError("Expected reviewed 2026-27 Division I membership of 300-400 teams")
    seen = set()
    selected = []
    for team in teams:
        if not isinstance(team, dict) or "teamId" not in team:
            raise ValueError("Provider team ID missing")
        key = str(team["teamId"])
        if key in ids:
            if key in seen:
                raise ValueError("Duplicate provider team ID")
            seen.add(key)
            selected.append(team)
    missing = ids - seen
    if missing:
        raise ValueError(f"{len(missing)} approved Division I teams missing from provider response")
    selected_players = []
    for player in players:
        if not isinstance(player, dict) or "teamId" not in player:
            raise ValueError("Provider player team ID missing")
        if str(player["teamId"]) in ids:
            selected_players.append(player)
    if not selected_players:
        raise ValueError("No Division I players found")
    return selected, selected_players


def load_approved_ids(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("season") != 2027 or payload.get("reviewed") is not True:
        raise ValueError("Season-specific reviewed Division I membership required")
    if not isinstance(payload.get("teamIds"), list):
        raise ValueError("teamIds list required")
    return payload["teamIds"]

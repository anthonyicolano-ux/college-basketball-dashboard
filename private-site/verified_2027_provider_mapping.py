"""Verified CBBD 2027 season field paths from 2026-11-19 schema-only API run.

Provider season team rows include non-DI teams (564 total); never call them
564 Division I teams. No provider requests or publication occur here.
The provider labels points.total as season total; convert to per-game explicitly.
"""
from math import isfinite

TEAM_PATHS = {
    "team": "team", "conference": "conference", "games": "games",
    "wins": "wins", "losses": "losses",
    "pointsTotal": "teamStats.points.total",
    "opponentPointsTotal": "opponentStats.points.total",
    "offRating": "teamStats.rating",
    "defRating": "opponentStats.rating",
}
PLAYER_PATHS = {
    "name": "name", "team": "team", "games": "games",
    "points": "points", "rebounds": "rebounds.total",
    "assists": "assists", "minutes": "minutes",
    "id": "athleteId",
}

def at(row, path):
    for part in path.split("."):
        if not isinstance(row, dict) or part not in row:
            raise ValueError("Missing provider path: " + path)
        row = row[part]
    if row is None:
        raise ValueError("Null provider path: " + path)
    return row

def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (float,int)) or not isfinite(value):
        raise ValueError("Invalid numeric field: " + label)
    return value

def map_team(row):
    mapped = {key: at(row,path) for key,path in TEAM_PATHS.items()}
    games = finite(mapped["games"],"games")
    if games <= 0:
        raise ValueError("Zero-game teams require separate handling")
    points = finite(mapped.pop("pointsTotal"),"team points")
    opp = finite(mapped.pop("opponentPointsTotal"),"opponent points")
    mapped["ppg"] = points / games
    mapped["oppPpg"] = opp / games
    mapped["scoringMargin"] = mapped["ppg"] - mapped["oppPpg"]
    mapped["netRating"] = finite(mapped["offRating"],"offRating") - finite(mapped["defRating"],"defRating")
    return mapped

def map_player(row):
    return {key: at(row,path) for key,path in PLAYER_PATHS.items()}

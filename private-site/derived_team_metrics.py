"""Offline, deterministic team metrics derived only from validated dashboard fields.

No provider requests, secrets, or publication. Never estimate possession-based
ratings from points per game: those require independently verified possessions.
"""
import math


def _number(row, key):
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Missing or invalid numeric input: {key}")
    return value


def derive_team_metrics(row):
    games = _number(row, "games")
    wins = _number(row, "wins")
    losses = _number(row, "losses")
    points = _number(row, "ppg")
    opponent_points = _number(row, "oppPpg")
    offensive_rating = _number(row, "offRating")
    defensive_rating = _number(row, "defRating")
    if any(value < 0 or int(value) != value for value in (games, wins, losses)):
        raise ValueError("Game counts must be nonnegative integers")
    if wins + losses != games:
        raise ValueError("Wins and losses must equal games played")
    if points < 0 or opponent_points < 0:
        raise ValueError("Points per game must be nonnegative")
    return {
        "winPct": round(wins / games, 4) if games else None,
        "calculatedScoringMargin": round(points - opponent_points, 2),
        "calculatedNetRating": round(offensive_rating - defensive_rating, 2),
    }

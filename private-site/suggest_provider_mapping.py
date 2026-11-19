"""Suggest candidate dashboard field paths from an offline schema inventory.

Suggestions are NOT verified mappings: review field meaning, units and season
before use. Prints only field paths and counts, never provider record values.
"""
import json
import sys
from pathlib import Path

TEAM_CANDIDATES = {
    "team": ("team", "team.name", "school", "school.name"),
    "conference": ("conference", "conference.name"),
    "games": ("games", "gamesPlayed", "stats.games"),
    "wins": ("wins", "record.wins"),
    "losses": ("losses", "record.losses"),
    "ppg": ("ppg", "pointsPerGame", "stats.pointsPerGame"),
    "oppPpg": ("oppPpg", "opponent.pointsPerGame"),
}
PLAYER_CANDIDATES = {
    "name": ("name", "player.name", "athlete.name"),
    "team": ("team", "team.name", "school"),
    "games": ("games", "gamesPlayed", "stats.games"),
    "points": ("points", "stats.points"),
    "rebounds": ("rebounds", "stats.rebounds"),
    "assists": ("assists", "stats.assists"),
    "minutes": ("minutes", "stats.minutes"),
}


def suggest(inventory, candidates):
    if not isinstance(inventory, dict) or not isinstance(inventory.get("paths"), list):
        raise ValueError("Expected an inventory object")
    paths = {p["path"]: p for p in inventory["paths"]}
    suggestions = {}
    for target, choices in candidates.items():
        matches = [path for path in choices if path in paths and
                   paths[path]["missing"] == 0]
        suggestions[target] = {"candidatePaths": matches,
                               "requiresReview": True}
    return suggestions


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: suggest_provider_mapping.py private-inventory.json")
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps({
        "warning": "Unverified suggestions only; not approved for publication",
        "teams": suggest(report["teams"], TEAM_CANDIDATES),
        "players": suggest(report["players"], PLAYER_CANDIDATES)
    }, indent=2))


if __name__ == "__main__":
    main()

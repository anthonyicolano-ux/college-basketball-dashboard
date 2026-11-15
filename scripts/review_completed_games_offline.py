"""Offline-only review of completed game records for eight known season-stat discrepancies.
No network access, provider credentials, KV writes, or publication.
Input is a private local JSON array of game records. Output is counts only.
Game schema/status semantics must be verified against actual CBBD response before use.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

TARGETS = ("Alabama A&M", "Central Connecticut State", "Cleveland State",
           "North Carolina A&T", "Princeton", "Quinnipiac",
           "Rhode Island", "Tennessee Tech")


def review(games, team_aliases):
    if not isinstance(games, list):
        raise ValueError("Expected game list")
    if not isinstance(team_aliases, dict):
        raise ValueError("Expected team alias dictionary")
    # Strict caller-supplied aliases; do not fuzzy-match team identities.
    aliases = {}
    for canonical in TARGETS:
        labels = team_aliases.get(canonical, [])
        if not isinstance(labels, list) or not all(isinstance(x, str) and x for x in labels):
            raise ValueError("Invalid aliases")
        for label in labels:
            if label in aliases and aliases[label] != canonical:
                raise ValueError("Ambiguous alias")
            aliases[label] = canonical
    counts = {team: Counter() for team in TARGETS}
    seen = set()
    for game in games:
        if not isinstance(game, dict):
            raise ValueError("Invalid game row")
        game_id = game.get("id")
        if not isinstance(game_id, (str, int)) or isinstance(game_id, bool):
            raise ValueError("Missing game ID")
        if game_id in seen:
            continue
        seen.add(game_id)
        home, away = game.get("homeTeam"), game.get("awayTeam")
        teams = {aliases[x] for x in (home, away) if isinstance(x, str) and x in aliases}
        # 'completed' and scores are explicit; no assumptions about status strings.
        completed = game.get("completed") is True
        home_score, away_score = game.get("homePoints"), game.get("awayPoints")
        score_valid = all(isinstance(x, int) and not isinstance(x, bool) and x >= 0
                          for x in (home_score, away_score))
        for team in teams:
            counts[team]["observed_games"] += 1
            if completed and score_valid and home_score != away_score:
                counts[team]["scored_completed_games"] += 1
                winner = home if home_score > away_score else away
                counts[team]["wins" if aliases.get(winner) == team else "losses"] += 1
            else:
                counts[team]["unresolved_status_or_score"] += 1
    return {"status": "OFFLINE_PARTIAL_COVERAGE_NOT_SEASON_RECONCILIATION",
            "unique_input_games": len(seen),
            "teams": {team: dict(sorted(counts[team].items())) for team in TARGETS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", required=True, type=Path)
    parser.add_argument("--aliases", required=True, type=Path)
    args = parser.parse_args()
    try:
        games = json.loads(args.games.read_text(encoding="utf-8"))
        aliases = json.loads(args.aliases.read_text(encoding="utf-8"))
        print("OFFLINE COMPLETED GAME REVIEW: " + json.dumps(review(games, aliases), sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        print("FAIL: offline review; input invalid. No raw records printed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

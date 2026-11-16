"""Offline-only review of completed game records for current season-stat discrepancies.
No network access, provider credentials, KV writes, or publication.
Input is a private local JSON array of game records. Output is counts only.
Game schema/status semantics must be verified against actual CBBD response before use.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

def review(games, team_aliases):
    if not isinstance(games, list):
        raise ValueError("Expected game list")
    if not isinstance(team_aliases, dict):
        raise ValueError("Expected team alias dictionary")
    targets = sorted(team_aliases)
    if not targets or len(targets) > 32 or any(not isinstance(x, str) or not x.strip() for x in targets):
        raise ValueError('Expected 1 to 32 named schools')
    # Strict caller-supplied aliases; do not fuzzy-match team identities.
    aliases = {}
    for canonical in targets:
        labels = team_aliases.get(canonical, [])
        if not isinstance(labels, list) or not all(isinstance(x, str) and x for x in labels):
            raise ValueError("Invalid aliases")
        for label in labels:
            if label in aliases and aliases[label] != canonical:
                raise ValueError("Ambiguous alias")
            aliases[label] = canonical
    counts = {team: Counter() for team in targets}
    schema_keys = ("id", "homeTeam", "awayTeam", "completed", "homePoints", "awayPoints")
    seen = set()
    for game in games:
        if not isinstance(game, dict):
            raise ValueError("Invalid game row")
        if any(field not in game for field in schema_keys):
            raise ValueError("Unverified game schema: required fields absent")
        if not isinstance(game["completed"], bool):
            raise ValueError("Unverified game completion semantics")
        if not isinstance(game["homeTeam"], str) or not isinstance(game["awayTeam"], str):
            raise ValueError("Invalid team identities")
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
            "teams": {team: dict(sorted(counts[team].items())) for team in targets}}


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

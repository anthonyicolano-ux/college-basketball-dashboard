"""Aggregate read-only game-quality diagnostics for two unresolved school records.

Exact labels are provisional, not verified team mappings. No raw games or IDs
are emitted. The capped response cannot establish full-season totals.
"""
from collections import Counter

TARGETS = ("Bethune-Cookman", "North Carolina A&T")


def inspect_targets(rows, targets=TARGETS):
    if not isinstance(rows, list) or len(rows) > 3000:
        raise ValueError("Expected bounded game list")
    if (not isinstance(targets, tuple) or not 1 <= len(targets) <= 32
            or any(not isinstance(x, str) or not x.strip() for x in targets)
            or len(set(targets)) != len(targets)):
        raise ValueError("Invalid target labels")
    counts = {target: Counter() for target in targets}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid game row")
        home, away = row.get("homeTeam"), row.get("awayTeam")
        for target in targets:
            if target not in (home, away):
                continue
            counts[target]["matched_rows"] += 1
            if row.get("status") != "final":
                counts[target]["nonfinal_or_unknown"] += 1
                continue
            counts[target]["final_rows"] += 1
            hp, ap = row.get("homePoints"), row.get("awayPoints")
            hw, aw = row.get("homeWinner"), row.get("awayWinner")
            valid_score = (all(isinstance(x, int) and not isinstance(x, bool) and x >= 0
                               for x in (hp, ap)) and hp != ap)
            valid_winner = (isinstance(hw, bool) and isinstance(aw, bool)
                            and hw != aw and valid_score and hw == (hp > ap))
            if valid_winner:
                counts[target]["validated_final"] += 1
            else:
                counts[target]["unresolved_final"] += 1
                if not valid_score:
                    counts[target]["invalid_or_tied_score"] += 1
                elif hw is None and aw is None:
                    counts[target]["missing_winner_flags_with_valid_score"] += 1
                elif not isinstance(hw, bool) or not isinstance(aw, bool):
                    counts[target]["partial_or_invalid_winner_flags"] += 1
                else:
                    counts[target]["contradictory_winner_flags"] += 1
    return {"coverage": "CAPPED_RESPONSE_NOT_SEASON_TOTALS",
            "identity_mapping": "EXACT_LABEL_ONLY_NOT_VERIFIED",
            "targets": {target: dict(sorted(counts[target].items())) for target in targets}}

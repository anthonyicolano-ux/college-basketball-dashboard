"""Offline membership evidence audit for the staged 2026-27 men's basketball candidates.

Compares candidate identities to the independently sourced official conference
roster snapshots already reviewed in audit_bulk_candidate_matching.py.
An aligned roster is conference evidence, NOT NCAA membership certification.
No API requests, no publication, no provider data.
"""
import json
from collections import Counter

from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from audit_bulk_candidate_matching import OFFICIAL_CONFERENCE_ROSTERS, key


def audit(reference, candidates):
    verified = validate_reference(reference)
    validate_candidates(candidates, verified)
    rows = candidates["candidates"]
    result = {}
    counts = Counter()
    for conference, roster in sorted(OFFICIAL_CONFERENCE_ROSTERS.items()):
        expected = {key(s) for s in roster["schools"]}
        actual = {key(row["name"]) for row in rows if row["conference"] == conference}
        # Names are compared literally after punctuation/case normalization; aliases
        # are not treated as proof of conference membership.
        aligned = actual == expected
        result[conference] = {
            "official_roster_size": len(expected),
            "candidate_roster_size": len(actual),
            "candidate_names_not_in_roster": len(actual - expected),
            "official_roster_names_not_in_candidates": len(expected - actual),
            "status": "ROSTER_ALIGNED_NOT_NCAA_VERIFIED" if aligned else "MANUAL_REVIEW_REQUIRED",
            "official_roster_source": roster["source"],
        }
        counts["conferences_checked"] += 1
        counts["conferences_aligned" if aligned else "conferences_needing_review"] += 1
        if aligned:
            counts["candidate_schools_with_conference_roster_evidence"] += len(actual)
    counts["staged_candidate_schools"] = len(rows)
    counts["candidate_schools_without_conference_roster_evidence"] = (
        len(rows) - counts["candidate_schools_with_conference_roster_evidence"]
    )
    return {
        "season": 2027,
        "sport": "mens_basketball",
        "counts": dict(sorted(counts.items())),
        "conference_results": result,
        "ncaa_school_level_membership": "NOT_VERIFIED_BY_THIS_AUDIT",
        "player_coverage": "NOT_CHECKED",
        "publication": "DISABLED",
        "note": "Conference roster alignment is preliminary independent evidence only; NCAA sport-specific membership must still be verified school by school.",
    }


def main():
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    report = audit(reference, candidates)
    print("OFFICIAL CONFERENCE ROSTER AUDIT: " + json.dumps(report, sort_keys=True))
    print("READ ONLY: zero API requests, zero KV writes, zero publications.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

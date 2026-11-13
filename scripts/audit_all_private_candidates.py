"""Read-only full staged-candidate coverage audit; no publication or API calls.

Roster alignment is independent conference evidence, not NCAA eligibility.
Provider team-stat availability is assessed separately by the existing preview script.
"""
import json
from collections import Counter
from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from audit_bulk_candidate_matching import OFFICIAL_CONFERENCE_ROSTERS, key


def audit(reference, candidate_file):
    verified = validate_reference(reference)
    validate_candidates(candidate_file, verified)
    candidates = candidate_file["candidates"]
    reference_schools = reference["schools"]
    roster_keys = {}
    for conference, roster in OFFICIAL_CONFERENCE_ROSTERS.items():
        roster_keys[conference] = {key(n) for n in roster["schools"]}
    counts = Counter()
    conferences = {}
    for candidate in candidates:
        conf = candidate.get("conference") or "(missing conference)"
        info = conferences.setdefault(conf, {"staged": 0, "conference_roster_evidence": 0, "needs_independent_evidence": 0})
        info["staged"] += 1
        counts["staged_candidates_checked"] += 1
        if key(candidate["name"]) in roster_keys.get(conf, set()):
            info["conference_roster_evidence"] += 1
            counts["candidates_with_independent_roster_evidence"] += 1
        else:
            info["needs_independent_evidence"] += 1
            counts["candidates_needing_independent_evidence"] += 1
        if candidate.get("verification_status") == "conflicting":
            counts["candidates_marked_conflicting"] += 1
    for conference, roster in OFFICIAL_CONFERENCE_ROSTERS.items():
        expected = roster_keys[conference]
        combined = {key(r["name"]) for r in [*reference_schools, *candidates] if r.get("conference") == conference}
        conferences.setdefault(conference, {"staged": 0, "conference_roster_evidence": 0, "needs_independent_evidence": 0})
        conferences[conference]["official_roster_alignment"] = (
            "ALIGNED" if combined == expected else "REVIEW_REQUIRED"
        )
        conferences[conference]["official_roster_source"] = roster["source"]
    return {
        "season": 2027,
        "sport": "mens_basketball",
        "scope": "ALL_STAGED_CANDIDATES",
        "counts": dict(sorted(counts.items())),
        "conferences": dict(sorted(conferences.items())),
        "ncaa_school_level_eligibility": "NOT_VERIFIED_BY_THIS_AUDIT",
        "team_stat_availability": "CHECK_SEPARATE_ONE_REQUEST_PREVIEW_STEP",
        "player_coverage": "NOT_CHECKED",
        "publication": "DISABLED",
        "note": "An official conference roster match is preliminary evidence, not independent NCAA sport-specific certification.",
    }


def main():
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    result = audit(reference, candidates)
    print("FULL CANDIDATE AUDIT: " + json.dumps(result, sort_keys=True))
    print("READ ONLY: zero API requests, zero KV writes, zero publications.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

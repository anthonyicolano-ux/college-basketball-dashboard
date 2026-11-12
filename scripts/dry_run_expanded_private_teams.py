"""Read-only expanded team coverage preview; never publishes or stores provider records."""
import json
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_bulk_candidate_matching import (
    OFFICIAL_CONFERENCE_ROSTERS, PROVIDER_NAME_ALIASES, key, same_conference,
)
from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from prepare_private_teams import prepare
from validate_multi_team_pilot import validate_rows

SEASON = 2027


def preview(records, reference, candidates):
    """Only verified-reference or officially cross-checked conference-roster schools."""
    eligible = {}
    for row in reference:
        eligible[row["name"]] = (row, "verified_reference")
    for conference, roster in OFFICIAL_CONFERENCE_ROSTERS.items():
        expected = {key(name) for name in roster["schools"]}
        staged = [c for c in candidates if c["conference"] == conference]
        if {key(c["name"]) for c in staged} != expected:
            raise ValueError("Official conference roster mismatch")
        for row in staged:
            if row["name"] not in eligible:
                eligible[row["name"]] = (row, "official_conference_roster")

    lookup = {}
    for name, (entry, _) in eligible.items():
        for alias in (name, *entry.get("aliases", []), *PROVIDER_NAME_ALIASES.get(name, ())):
            k = key(alias)
            if k in lookup and lookup[k] != name:
                raise ValueError("Ambiguous identity alias")
            lookup[k] = name

    accepted = {}
    rejected = Counter()
    for record in records:
        if not isinstance(record, dict) or record.get("season") != SEASON:
            rejected["invalid_record_or_season"] += 1
            continue
        name = record.get("team")
        if not isinstance(name, str) or key(name) not in lookup:
            rejected["outside_approved_scope"] += 1
            continue
        identity = lookup[key(name)]
        entry, _ = eligible[identity]
        if identity in accepted:
            rejected["duplicate_identity"] += 1
            del accepted[identity]
            continue
        if not record.get("conference") or not same_conference(entry["conference"], str(record["conference"])):
            rejected["conference_disagreement_or_missing"] += 1
            continue
        try:
            data = prepare([record])
            row = data["rows"][0]
            if row["games"] != row["wins"] + row["losses"]:
                rejected["game_count_inconsistent"] += 1
                continue
            validate_rows([row, {**row, "team": "__temporary__", "conference": "__other__"}], 2, 2)
            accepted[identity] = record
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            rejected["incomplete_or_invalid_metrics"] += 1

    if len(accepted) < 5:
        raise ValueError("Insufficient validated teams for expanded preview")
    dataset = prepare(list(accepted.values()))
    rows = dataset["rows"]
    validate_rows(rows, min_teams=5, max_teams=30)
    return {
        "eligible_reference_entries": len(eligible),
        "validated_teams": len(rows),
        "conferences": len({r["conference"] for r in rows}),
        "excluded_counts": dict(sorted(rejected.items())),
        "publication": "DISABLED",
        "note": "Conference-roster verification is not independent NCAA eligibility certification. No candidate outside two officially checked conference rosters is accepted.",
    }


def main():
    try:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        verified = validate_reference(reference)
        validate_candidates(candidates, verified)
        token = os.environ.get("CBBD_API_KEY", "").strip()
        if not token:
            raise ValueError("Missing API credential")
        url = "https://api.collegebasketballdata.com/stats/team/season?" + urlencode({"season": SEASON, "seasonType": "regular"})
        with urlopen(Request(url, headers={"Authorization": "Bearer " + token, "Accept": "application/json"}), timeout=40) as response:
            records = json.load(response)
        if not isinstance(records, list):
            raise ValueError("Unexpected provider response")
        result = preview(records, reference["schools"], candidates["candidates"])
        print("EXPANDED PRIVATE TEAM PREVIEW: " + json.dumps(result, sort_keys=True))
        print("DRY RUN: one CBBD request; no provider records logged, saved, uploaded or published.")
        return 0
    except Exception as error:
        print("FAIL: expanded private preview; error_type=" + type(error).__name__ + "; no records or credentials printed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

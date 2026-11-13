"""Read-only preview of potential team coverage beyond the current 24-team pilot.

One CBBD team-season API request. Candidate identities are NOT eligibility approval.
Never logs individual provider rows, stores datasets, or writes Cloudflare KV.
"""
import json
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import (
    REFERENCE, CANDIDATES, validate_reference, validate_candidates,
)
from audit_bulk_candidate_matching import (
    PROVIDER_NAME_ALIASES, key, same_conference,
)
from dry_run_private_players import approved_names
from prepare_private_teams import prepare


def preview(records, candidates, current_lookup):
    if not isinstance(records, list):
        raise ValueError("Invalid provider response")
    current_names = set(current_lookup.values())
    prospective = {}
    aliases = {}
    ambiguous = set()
    for item in candidates:
        name = item["name"]
        if name in current_names:
            continue
        for label in (name, *item.get("aliases", []), *PROVIDER_NAME_ALIASES.get(name, ())):
            k = key(label)
            if k in aliases and aliases[k] != name:
                ambiguous.add(k)
            else:
                aliases[k] = name

    excluded = Counter()
    accepted = {}
    blocked = set()
    for record in records:
        if not isinstance(record, dict) or record.get("season") != 2027:
            excluded["invalid_season_or_record"] += 1
            continue
        provider_name = record.get("team")
        if not isinstance(provider_name, str):
            excluded["missing_name"] += 1
            continue
        k = key(provider_name)
        if k in ambiguous:
            excluded["ambiguous_alias"] += 1
            continue
        name = aliases.get(k)
        if name is None:
            excluded["outside_new_candidate_scope"] += 1
            continue
        if name in blocked:
            excluded["duplicate_identity"] += 1
            continue
        if name in accepted:
            del accepted[name]
            blocked.add(name)
            excluded["duplicate_identity"] += 1
            continue
        prospective[name] = True
        item = next(x for x in candidates if x["name"] == name)
        if not record.get("conference") or not same_conference(item["conference"], str(record["conference"])):
            excluded["conference_mismatch"] += 1
            continue
        try:
            data = prepare([record])["rows"][0]
            if data["games"] <= 0 or data["games"] != data["wins"] + data["losses"]:
                excluded["invalid_game_record"] += 1
                continue
            accepted[name] = item["conference"]
        except (ValueError, TypeError, KeyError, ZeroDivisionError, IndexError):
            excluded["invalid_statistics"] += 1

    by_conference = Counter(accepted.values())
    return {
        "current_pilot_teams": len(current_names),
        "additional_candidate_records_matched": len(prospective),
        "additional_teams_passing_preliminary_checks": len(accepted),
        "potential_total_if_independently_verified": len(current_names) + len(accepted),
        "conferences_with_preliminary_additions": dict(sorted(by_conference.items())),
        "excluded_counts": dict(sorted(excluded.items())),
        "membership_verification": "REQUIRED_BEFORE_PUBLICATION",
        "player_coverage": "NOT_YET_CHECKED",
        "publication": "DISABLED",
    }


def main():
    if os.environ.get("PUBLISH_EXPANDED_KV") or os.environ.get("PUBLICATION_APPROVAL"):
        print("BLOCKED: this workflow is dry-run only; no API request.")
        return 2
    stage = "load_reference"
    try:
        ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
        stage = "load_candidates"
        candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        stage = "validate_reference"
        verified = validate_reference(ref)
        stage = "validate_candidates"
        validate_candidates(candidates, verified)
        stage = "load_approved_names"
        lookup = approved_names()
        token = os.environ.get("CBBD_API_KEY", "").strip()
        if not token:
            print("BLOCKED: CBBD API key missing; no request.")
            return 2
        url = "https://api.collegebasketballdata.com/stats/team/season?" + urlencode(
            {"season": 2027, "seasonType": "regular"}
        )
        stage = "fetch_provider_response"
        with urlopen(Request(url, headers={
            "Authorization": "Bearer " + token, "Accept": "application/json"
        }), timeout=50) as response:
            stage = "parse_provider_response"
            records = json.load(response)
        stage = "preview_team_statistics"
        report = preview(records, candidates["candidates"], lookup)
        print("PRELIMINARY EXPANSION AUDIT: " + json.dumps(report, sort_keys=True))
        print("DRY RUN: one provider request; zero KV writes, artifacts, or raw provider rows.")
        return 0
    except Exception as error:
        print("FAIL: expansion audit; stage=" + stage +
              "; error_type=" + type(error).__name__ +
              "; no provider records or credentials logged.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

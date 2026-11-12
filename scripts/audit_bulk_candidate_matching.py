"""Read-only bulk candidate/provider reconciliation. One season API request; aggregate logs only."""
import difflib
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import (
    REFERENCE, CANDIDATES, validate_reference, validate_candidates,
)
from transform_cbbd import team_row


def key(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", value)


def reconcile(records, verified, candidates):
    lookup = defaultdict(set)
    entries = {}
    for label, rows in (("verified", verified), ("candidate", candidates)):
        for row in rows:
            identifier = (label, row["name"])
            entries[identifier] = row
            for name in [row["name"], *row.get("aliases", [])]:
                lookup[key(name)].add(identifier)

    counts = Counter()
    matched = set()
    by_conference = Counter()
    seen_provider = set()
    unresolved = []
    for record in records:
        if not isinstance(record, dict) or record.get("season") != 2027:
            counts["invalid_season_or_record"] += 1
            continue
        name = record.get("team")
        if not isinstance(name, str) or not name.strip():
            counts["missing_identity"] += 1
            continue
        normalized = key(name)
        if normalized in seen_provider:
            counts["duplicate_provider_identity"] += 1
        seen_provider.add(normalized)
        options = lookup.get(normalized, set())
        if len(options) != 1:
            counts["ambiguous_matches" if options else "unmatched_provider_records"] += 1
            unresolved.append(name)
            continue
        identifier = next(iter(options))
        matched.add(identifier)
        counts["verified_matches" if identifier[0] == "verified" else "candidate_matches_unverified"] += 1
        entry = entries[identifier]
        by_conference[entry["conference"]] += 1
        if record.get("conference"):
            if key(str(record["conference"])) != key(entry["conference"]):
                counts["conference_label_differences_unreviewed"] += 1
        else:
            counts["missing_provider_conference"] += 1
        try:
            row = team_row(record)
            values = (row.get("games"), row.get("wins"), row.get("losses"))
            if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
                gap = values[0] - values[1] - values[2]
                if gap != 0:
                    counts["game_count_discrepancies"] += 1
                    if gap == 1:
                        counts["one_game_gaps"] += 1
            else:
                counts["missing_game_count_fields"] += 1
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            counts["transform_errors"] += 1

    candidate_names = {("candidate", x["name"]) for x in candidates}
    counts["unmatched_candidates"] = len(candidate_names - matched)
    counts["candidate_total"] = len(candidates)
    counts["provider_records"] = len(records)
    counts["matched_unique_entries"] = len(matched)
    # Fuzzy matches are diagnostic ONLY; never use them to establish eligibility.
    candidate_keys = {key(x["name"]) for x in candidates}
    counts["unmatched_provider_with_similar_candidate_name"] = sum(
        bool(difflib.get_close_matches(key(n), candidate_keys, n=1, cutoff=0.82))
        for n in unresolved
    )
    return {
        "season": 2027,
        "eligibility": "UNVERIFIED_FOR_CANDIDATES",
        "publication": "DISABLED",
        "counts": dict(sorted(counts.items())),
        "matched_conference_groups": len(by_conference),
        "note": "Matches are name comparisons only, not NCAA membership confirmation. Conference label differences require manual mapping."
    }


def main():
    try:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        candidate_file = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        verified_index = validate_reference(reference)
        validate_candidates(candidate_file, verified_index)
        token = os.environ.get("CBBD_API_KEY", "").strip()
        if not token:
            raise ValueError("Missing API credential")
        url = "https://api.collegebasketballdata.com/stats/team/season?" + urlencode(
            {"season": 2027, "seasonType": "regular"})
        with urlopen(Request(url, headers={
            "Authorization": "Bearer " + token, "Accept": "application/json"
        }), timeout=40) as response:
            records = json.load(response)
        if not isinstance(records, list):
            raise ValueError("Unexpected provider payload")
        report = reconcile(records, reference["schools"], candidate_file["candidates"])
        print("BULK MATCH AUDIT: " + json.dumps(report, sort_keys=True))
        print("DRY RUN: one CBBD request; no provider rows, credentials, KV writes, artifacts or publication.")
        return 0
    except Exception as error:
        print("FAIL: bulk audit; error_type=" + type(error).__name__ + "; no private data logged.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

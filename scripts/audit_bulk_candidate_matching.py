"""Read-only bulk candidate/provider reconciliation. One season API request; aggregate logs only."""
import difflib
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
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


# Explicit, non-eligibility name aliases. These are matching hints, not proof of NCAA membership.
# Avoid general fuzzy auto-matching, which can confuse distinct schools.
PROVIDER_NAME_ALIASES = {
    "Miami (Florida)": ("Miami", "Miami FL"),
    "Miami (Ohio)": ("Miami OH",),
    "Saint Joseph's": ("St. Joseph's", "Saint Josephs"),
    "St. Bonaventure": ("Saint Bonaventure",),
    "Saint Mary's": ("St. Mary's", "Saint Marys"),
    "San José State": ("San Jose State",),
    "Hawai'i": ("Hawaii",),
    "NC State": ("North Carolina State",),
    "UAlbany": ("Albany",),
    "UMass": ("Massachusetts",),
    "USF": ("South Florida",),
    "FIU": ("Florida International",),
    "FGCU": ("Florida Gulf Coast",),
    "UIC": ("Illinois Chicago",),
    "IU Indy": ("IUPUI",),
    "FDU": ("Fairleigh Dickinson",),
    "LIU": ("Long Island",),
    "UTRGV": ("UT Rio Grande Valley",),
    "SE Louisiana": ("Southeastern Louisiana",),
    "UL Monroe": ("Louisiana Monroe",),
    "App State": ("Appalachian State",),
    "Southern Miss": ("Southern Mississippi",),
    "UT Arlington": ("Texas Arlington",),
    "Cal Poly": ("Cal Poly SLO",),
    "Cal State Bakersfield": ("CSU Bakersfield",),
    "Cal State Fullerton": ("CSU Fullerton",),
    "Cal State Northridge": ("CSU Northridge",),
}
# A conference's full name and abbreviation are the same conference.
# Do not map membership changes here: those need separate season-specific evidence.
CONFERENCE_ALIASES = {
    "ACC": ("Atlantic Coast", "Atlantic Coast Conference"),
    "Big 12": ("Big 12 Conference",),
    "Big East": ("Big East Conference",),
    "Pac-12": ("Pac 12", "Pac-12 Conference"),
    "Big Ten": ("Big Ten Conference",),
    "SEC": ("Southeastern", "Southeastern Conference"),
    "ASUN": ("Atlantic Sun", "ASUN Conference"),
    "CAA": ("Coastal Athletic Association",),
    "MAC": ("Mid-American", "Mid-American Conference"),
    "MEAC": ("Mid-Eastern Athletic Conference",),
    "SWAC": ("Southwestern Athletic Conference",),
    "WCC": ("West Coast", "West Coast Conference"),
    "UAC": ("United Athletic Conference",),
    "Metro": ("Metro Conference",),  # Season-specific renaming needs explicit evidence
    "American": ("American Athletic", "American Athletic Conference"),
    "Atlantic 10": ("Atlantic 10 Conference", "A-10"),
    "Mountain West": ("Mountain West Conference",),
    "Missouri Valley": ("Missouri Valley Conference", "MVC"),
    "Sun Belt": ("Sun Belt Conference",),
    "Southland": ("Southland Conference",),
    "SoCon": ("Southern Conference",),
    "OVC": ("Ohio Valley Conference",),
    "NEC": ("Northeast Conference",),
    "Ivy": ("Ivy League",),
    "Horizon": ("Horizon League",),
    "Big Sky": ("Big Sky Conference",),
    "Big South": ("Big South Conference",),
    "Big West": ("Big West Conference",),
    "America East": ("America East Conference", "Am. East"),
    "Patriot": ("Patriot League",),
    "Summit": ("Summit League",),
    "Conference USA": ("C-USA",),
}
def same_conference(expected, observed):
    return key(observed) in {key(expected), *(key(x) for x in CONFERENCE_ALIASES.get(expected, ()))}

# Official 2026-27 men's basketball conference rosters, checked 2026-11-12.
# These verify conference roster listings only, not independent NCAA eligibility.
OFFICIAL_CONFERENCE_ROSTERS = {
    "America East": {
        "source": "https://americaeast.com/standings.aspx?path=mbball",
        "schools": ("Binghamton", "Bryant", "Maine", "New Hampshire", "NJIT", "UAlbany", "UMass Lowell", "UMBC", "Vermont"),
    },
    "Missouri Valley": {
        "source": "https://mvc-sports.com/sports/2022/11/3/MBB_1103224612.aspx",
        "schools": ("Belmont", "Bradley", "Drake", "Evansville", "UIC", "Illinois State", "Indiana State", "Murray State", "Northern Iowa", "Southern Illinois", "Valparaiso"),
    },
}

def official_roster_audit(candidates):
    """Compare candidate reference against official conference rosters, not provider labels."""
    result = {}
    for conference, roster in OFFICIAL_CONFERENCE_ROSTERS.items():
        expected = {key(name) for name in roster["schools"]}
        actual = {key(row["name"]) for row in candidates if row["conference"] == conference}
        result[conference] = {
            "official_roster_count": len(expected),
            "candidate_count": len(actual),
            "candidate_names_missing_from_official_roster": len(actual - expected),
            "official_names_missing_from_candidates": len(expected - actual),
            "roster_alignment": "MATCH" if actual == expected else "REVIEW",
            "source": roster["source"],
        }
    return result

def reconcile(records, verified, candidates):
    lookup = defaultdict(set)
    entries = {}
    for label, rows in (("verified", verified), ("candidate", candidates)):
        for row in rows:
            identifier = (label, row["name"])
            entries[identifier] = row
            for name in [row["name"], *row.get("aliases", []), *PROVIDER_NAME_ALIASES.get(row["name"], ())]:
                lookup[key(name)].add(identifier)

    counts = Counter()
    matched = set()
    by_conference = Counter()
    seen_provider = set()
    unresolved = []
    conference_difference_groups = Counter()
    conference_difference_label_groups = defaultdict(Counter)
    official_roster_conflicts = Counter()
    unmatched_candidate_name_diagnostics = Counter()
    unmatched_candidate_fuzzy_strength = Counter()
    unmatched_candidate_groups = Counter()
    ambiguous_alias_keys = sum(len(ids) > 1 for ids in lookup.values())
    alias_matches = 0
    exact_matches = 0
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
        if normalized == key(identifier[1]):
            exact_matches += 1
        else:
            alias_matches += 1
        counts["verified_matches" if identifier[0] == "verified" else "candidate_matches_unverified"] += 1
        entry = entries[identifier]
        by_conference[entry["conference"]] += 1
        if record.get("conference"):
            if not same_conference(entry["conference"], str(record["conference"])):
                counts["conference_label_differences_unreviewed"] += 1
                conference_difference_groups[entry["conference"]] += 1
                # Aggregate provider labels only: never print individual team rows.
                conference_difference_label_groups[entry["conference"]][str(record["conference"]).strip() or "(blank)"] += 1
                if entry["conference"] in OFFICIAL_CONFERENCE_ROSTERS:
                    official_roster_conflicts[entry["conference"]] += 1
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
    for identifier in candidate_names - matched:
        unmatched_candidate_groups[entries[identifier]["conference"]] += 1
    # Diagnose unmatched candidates without leaking team identities or provider rows.
    unresolved_keys = [key(name) for name in unresolved]
    for identifier in candidate_names - matched:
        names = [entries[identifier]["name"], *entries[identifier].get("aliases", []), *PROVIDER_NAME_ALIASES.get(identifier[1], ())]
        best_score = max(
            (difflib.SequenceMatcher(None, key(name), provider_key).ratio()
             for name in names for provider_key in unresolved_keys),
            default=0.0,
        )
        if best_score >= 0.82:
            unmatched_candidate_name_diagnostics[entries[identifier]["conference"]] += 1
            unmatched_candidate_fuzzy_strength["high_0_95_plus" if best_score >= 0.95 else "review_0_82_to_0_95"] += 1
    counts["unmatched_candidates"] = len(candidate_names - matched)
    counts["ambiguous_alias_keys_in_reference"] = ambiguous_alias_keys
    counts["exact_name_matches"] = exact_matches
    counts["explicit_alias_matches"] = alias_matches
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
        "official_conference_roster_checks": official_roster_audit(candidates),
        "unmatched_candidate_counts_by_conference": dict(sorted(unmatched_candidate_groups.items())),
        "unmatched_candidates_with_similar_provider_name_by_conference": dict(sorted(unmatched_candidate_name_diagnostics.items())),
        "unmatched_candidate_fuzzy_strength_counts": dict(sorted(unmatched_candidate_fuzzy_strength.items())),
        "provider_conference_labels_by_expected_conference": {k: dict(sorted(v.items())) for k, v in sorted(conference_difference_label_groups.items())},
        "official_roster_provider_conflict_counts": dict(sorted(official_roster_conflicts.items())),
        "conference_difference_counts_by_expected_conference": dict(sorted(conference_difference_groups.items())),
        "note": "Official roster alignment is independent of provider conference labels. Provider label disagreements are not auto-corrected. Candidate names and fuzzy matches remain unverified; diagnostics do not authorize publication."
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

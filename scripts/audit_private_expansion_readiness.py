"""Read-only consolidated expansion readiness audit. Two CBBD requests maximum.
No raw provider records, player names, credentials, artifacts or KV writes are logged.
Conference roster evidence is NOT independent NCAA sport-specific membership approval.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from audit_bulk_candidate_matching import OFFICIAL_CONFERENCE_ROSTERS, PROVIDER_NAME_ALIASES, key, same_conference
from verify_next_private_membership import audit as membership_audit
from dry_run_private_players import approved_names, audit as player_audit
from preview_next_private_team_expansion import preview as team_preview
from prepare_private_teams import prepare
from transform_cbbd import player_row

SEASON = 2027
MIN_GAMES = 5


def fetch(endpoint, token):
    url = "https://api.collegebasketballdata.com/" + endpoint + "?" + urlencode(
        {"season": SEASON, "seasonType": "regular"})
    with urlopen(Request(url, headers={
        "Authorization": "Bearer " + token, "Accept": "application/json"
    }), timeout=50) as response:
        return json.load(response)


def evaluate(teams, players, reference, candidates):
    verified = validate_reference(reference)
    validate_candidates(candidates, verified)
    membership = membership_audit(reference, candidates)
    lookup = approved_names()
    candidate_rows = candidates["candidates"]
    preview = team_preview(teams, candidate_rows, lookup)
    player_summary = player_audit(players, lookup)
    staged = {item["name"]: item for item in candidate_rows}
    aliases = defaultdict(set)
    for name, item in staged.items():
        for label in (name, *item.get("aliases", []), *PROVIDER_NAME_ALIASES.get(name, ())):
            aliases[key(label)].add(name)
    team_games = defaultdict(list)
    for source in teams:
        if not isinstance(source, dict) or source.get("season") != SEASON:
            continue
        names = aliases.get(key(source.get("team", "")))
        if not names or len(names) != 1:
            continue
        name = next(iter(names))
        if not source.get("conference") or not same_conference(staged[name]["conference"], str(source["conference"])):
            continue
        try:
            row = prepare([source])["rows"][0]
            if row["games"] > 0 and row["games"] == row["wins"] + row["losses"]:
                team_games[name].append(row["games"])
        except (ValueError, TypeError, KeyError, ZeroDivisionError, IndexError):
            pass
    player_counts = Counter()
    player_names = defaultdict(set)
    for source in players:
        if not isinstance(source, dict) or source.get("season") != SEASON:
            continue
        canonical = lookup.get(key(source.get("team", "")))
        if canonical not in staged:
            continue
        try:
            row = player_row(source)
            if row["games"] > 0 and row["name"].strip():
                player_names[canonical].add(row["name"].strip().casefold())
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            pass
    for name, names in player_names.items():
        player_counts[name] = len(names)
    reasons = Counter()
    categories = Counter()
    examples = defaultdict(list)
    for name, item in sorted(staged.items()):
        conference = item["conference"]
        evidence = membership["conference_results"].get(conference, {})
        issues = []
        if evidence.get("status") != "ROSTER_ALIGNED_NOT_NCAA_VERIFIED":
            issues.append("conference_roster_evidence_missing")
        if len(team_games[name]) != 1:
            issues.append("team_statistics_missing_or_ambiguous")
        elif team_games[name][0] < MIN_GAMES:
            issues.append("fewer_than_five_team_games")
        if player_counts[name] == 0:
            issues.append("no_player_statistics")
        # Independent NCAA sport-specific membership verification is not
        # represented by conference roster matching and remains mandatory.
        issues.append("ncaa_sport_membership_not_independently_verified")
        for issue in issues:
            reasons[issue] += 1
        if issues == ["ncaa_sport_membership_not_independently_verified"]:
            category = "data_ready_pending_ncaa_verification"
        else:
            category = "requires_data_or_evidence_review"
        categories[category] += 1
        if len(examples[category]) < 12:
            examples[category].append(name)
    return {
        "season": SEASON,
        "staged_candidate_count": len(staged),
        "minimum_team_games": MIN_GAMES,
        "readiness_categories": dict(sorted(categories.items())),
        "issue_counts": dict(sorted(reasons.items())),
        "sample_school_names_by_category": dict(sorted(examples.items())),
        "conference_roster_evidence": membership["counts"],
        "team_coverage": preview,
        "player_coverage": player_summary,
        "schedule_identity_crosscheck": "NOT_RUN_NO_SCHEDULE_REQUEST",
        "ncaa_sport_specific_membership": "NOT_INDEPENDENTLY_VERIFIED",
        "publication": "DISABLED",
        "note": "Data readiness is not eligibility approval. All schools require independent NCAA sport-specific verification before expansion."
    }


def main():
    if os.getenv("PUBLISH_EXPANDED_KV") or os.getenv("PUBLICATION_APPROVAL"):
        print("BLOCKED: read-only audit cannot publish.")
        return 2
    stage = "initialize"
    try:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        token = os.environ.get("CBBD_API_KEY", "").strip()
        if not token:
            raise ValueError("Missing API key")
        stage = "fetch_team_statistics"
        teams = fetch("stats/team/season", token)
        stage = "fetch_player_statistics"
        players = fetch("stats/player/season", token)
        stage = "evaluate_readiness"
        report = evaluate(teams, players, reference, candidates)
        print("CONSOLIDATED PRIVATE EXPANSION READINESS: " + json.dumps(report, sort_keys=True))
        print("READ ONLY: two provider requests; zero KV writes, artifacts, raw provider rows, or publications.")
        return 0
    except Exception as error:
        print("FAIL: consolidated readiness; stage=" + stage + "; error_type=" +
              type(error).__name__ + "; no provider rows or credentials logged.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

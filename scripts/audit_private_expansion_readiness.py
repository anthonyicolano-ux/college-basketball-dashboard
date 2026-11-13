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
from dry_run_private_players import audit as player_audit
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
    candidate_rows = candidates["candidates"]
    staged = {item["name"]: item for item in candidate_rows}
    # Match every staged school, not just the seven conferences with roster evidence.
    # Preserve ambiguous aliases as unresolved rather than assigning them arbitrarily.
    aliases = defaultdict(set)
    for item in (*reference["schools"], *candidate_rows):
        name = item["name"]
        for label in (name, *item.get("aliases", []), *PROVIDER_NAME_ALIASES.get(name, ())):
            aliases[key(label)].add(name)
    lookup = {label: next(iter(names)) for label, names in aliases.items() if len(names) == 1}
    player_summary = player_audit(players, lookup)
    diagnostics = Counter()
    team_provider_names = set()
    player_provider_names = set()
    team_name_matches = set()
    player_name_matches = set()
    team_games = defaultdict(list)
    team_validation_reasons = defaultdict(Counter)
    for source in teams:
        if not isinstance(source, dict) or source.get("season") != SEASON:
            continue
        label = source.get("team")
        if not isinstance(label, str) or not label.strip():
            diagnostics["team_records_missing_identity"] += 1
            continue
        team_provider_names.add(key(label))
        names = aliases.get(key(label), set())
        if len(names) > 1:
            diagnostics["team_records_ambiguous_alias"] += 1
            continue
        name = lookup.get(key(label))
        if name not in staged:
            diagnostics["team_records_unmatched_to_staged"] += 1
            continue
        team_name_matches.add(name)
        if not source.get("conference") or not same_conference(staged[name]["conference"], str(source["conference"])):
            diagnostics["team_records_conference_missing_or_different"] += 1
            team_validation_reasons[name]["conference_missing_or_different"] += 1
            continue
        try:
            row = prepare([source])["rows"][0]
            if row["games"] <= 0:
                team_validation_reasons[name]["nonpositive_games"] += 1
            elif row["games"] != row["wins"] + row["losses"]:
                team_validation_reasons[name]["games_wins_losses_mismatch"] += 1
            else:
                team_games[name].append(row["games"])
        except (ValueError, TypeError, KeyError, ZeroDivisionError, IndexError):
            team_validation_reasons[name]["team_stat_transform_failed"] += 1
    player_counts = Counter()
    player_names = defaultdict(set)
    for source in players:
        if not isinstance(source, dict) or source.get("season") != SEASON:
            continue
        label = source.get("team")
        if not isinstance(label, str) or not label.strip():
            diagnostics["player_records_missing_identity"] += 1
            continue
        player_provider_names.add(key(label))
        if len(aliases.get(key(label), set())) > 1:
            diagnostics["player_records_ambiguous_alias"] += 1
            continue
        canonical = lookup.get(key(label))
        if canonical not in staged:
            diagnostics["player_records_unmatched_to_staged"] += 1
            continue
        player_name_matches.add(canonical)
        try:
            row = player_row(source)
            if row["games"] > 0 and row["name"].strip():
                player_names[canonical].add(row["name"].strip().casefold())
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            pass
    for name, names in player_names.items():
        player_counts[name] = len(names)
    # Distinguish a missing provider identity from records that match but fail validation.
    diagnostics["staged_teams_without_matching_team_identity"] = len(set(staged) - team_name_matches)
    diagnostics["staged_teams_without_matching_player_identity"] = len(set(staged) - player_name_matches)
    diagnostics["distinct_provider_team_names"] = len(team_provider_names)
    diagnostics["distinct_provider_player_team_names"] = len(player_provider_names)
    diagnostics["ambiguous_alias_keys"] = sum(len(names) > 1 for names in aliases.values())
    unresolved_schools = defaultdict(list)
    reasons = Counter()
    categories = Counter()
    examples = defaultdict(list)
    coverage = Counter()
    for name, item in sorted(staged.items()):
        conference = item["conference"]
        evidence = membership["conference_results"].get(conference, {})
        has_team_stats = len(team_games[name]) == 1
        has_player_stats = player_counts[name] > 0
        has_five_games = has_team_stats and team_games[name][0] >= MIN_GAMES
        conference_evidence = evidence.get("status") == "ROSTER_ALIGNED_NOT_NCAA_VERIFIED"
        # Statistical availability and ranking maturity are not eligibility approval.
        if has_team_stats:
            coverage["team_stats_available_any_games"] += 1
        if has_player_stats:
            coverage["player_stats_available_any_games"] += 1
        if has_team_stats and has_player_stats:
            coverage["team_and_player_stats_available_any_games"] += 1
        if has_five_games:
            coverage["team_stats_meet_five_game_ranking_threshold"] += 1
        if conference_evidence and has_team_stats and has_player_stats:
            coverage["data_coverage_ready_pending_independent_eligibility"] += 1
        issues = []
        if evidence.get("status") != "ROSTER_ALIGNED_NOT_NCAA_VERIFIED":
            issues.append("conference_roster_evidence_missing")
        if len(team_games[name]) != 1:
            issues.append("team_statistics_missing_or_ambiguous")
        elif team_games[name][0] < MIN_GAMES:
            issues.append("fewer_than_five_team_games")
        if player_counts[name] == 0:
            issues.append("player_statistics_missing_or_invalid" if name in player_name_matches else "player_identity_not_matched")
        # Independent NCAA sport-specific membership verification is not
        # represented by conference roster matching and remains mandatory.
        issues.append("ncaa_sport_membership_not_independently_verified")
        for issue in issues:
            reasons[issue] += 1
            if issue in ("team_statistics_missing_or_ambiguous", "player_statistics_missing_or_invalid", "player_identity_not_matched", "fewer_than_five_team_games"):
                unresolved_schools[issue].append(name)
        if issues == ["ncaa_sport_membership_not_independently_verified"]:
            category = "data_ready_pending_ncaa_verification"
        else:
            category = "requires_data_or_evidence_review"
        categories[category] += 1
        if len(examples[category]) < 12:
            examples[category].append(name)
    # Concise, actionable school-level exceptions. No provider rows or player identities.
    # Under-five-game schools are ranking-ineligible, not statistical exceptions.
    actionable_reasons = (
        "team_statistics_missing_or_ambiguous",
        "player_statistics_missing_or_invalid",
        "player_identity_not_matched",
    )
    exception_names = sorted(set().union(
        *(set(unresolved_schools[reason]) for reason in actionable_reasons)
    ))
    # Cross-check identity presence across the two already fetched provider datasets.
    # This never auto-assigns aliases and does not require an additional API request.
    identity_crosscheck = {
        "team_missing_but_player_identity_matched": sorted(
            name for name in exception_names
            if name not in team_name_matches and name in player_name_matches
        ),
        "player_missing_but_team_identity_matched": sorted(
            name for name in exception_names
            if name not in player_name_matches and name in team_name_matches
        ),
        "both_team_and_player_identity_missing": sorted(
            name for name in exception_names
            if name not in team_name_matches and name not in player_name_matches
        ),
    }
    exception_report = []
    for name in exception_names:
        issues = [reason for reason, schools in sorted(unresolved_schools.items())
                  if name in schools]
        exception_report.append({
            "school": name,
            "issues": issues,
            "team_identity_matched": name in team_name_matches,
            "player_identity_matched": name in player_name_matches,
            "valid_team_record_count": len(team_games[name]),
            "team_validation_reasons": dict(sorted(team_validation_reasons[name].items())),
            "validated_player_count": player_counts[name],
            "team_games": team_games[name][0] if len(team_games[name]) == 1 else None,
            "conference_roster_evidence": membership["conference_results"].get(
                staged[name]["conference"], {}).get("status", "NOT_CHECKED"),
            "ncaa_sport_membership": "PENDING_INDEPENDENT_VERIFICATION",
        })
    exception_summary = {
        "schools_requiring_statistical_review": len(exception_report),
        "team_statistics_exceptions": len(unresolved_schools["team_statistics_missing_or_ambiguous"]),
        "player_identity_exceptions": len(unresolved_schools["player_identity_not_matched"]),
        "player_statistics_invalid_exceptions": len(unresolved_schools["player_statistics_missing_or_invalid"]),
        "under_five_games_ranking_only": len(unresolved_schools["fewer_than_five_team_games"]),
        "notes": "Exceptions may overlap. Under-five-games affects rankings, not basic stats display.",
    }
    return {
        "season": SEASON,
        "staged_candidate_count": len(staged),
        "minimum_team_games": MIN_GAMES,
        "readiness_categories": dict(sorted(categories.items())),
        "separate_coverage_gates": {
            "basic_team_and_player_display": "VALID_STATISTICS_ANY_POSITIVE_GAME_COUNT; REQUIRES_SEPARATE_ELIGIBILITY_APPROVAL",
            "ranked_matchup_analysis": "BOTH_OPPONENTS_REQUIRE_AT_LEAST_FIVE_GAMES_AND_APPROVED_COVERAGE",
            "publication_eligibility": "INDEPENDENT_NCAA_SPORT_SPECIFIC_VERIFICATION_REQUIRED",
            "counts": dict(sorted(coverage.items()))
        },
        "issue_counts": dict(sorted(reasons.items())),
        "statistical_exception_summary": exception_summary,
        "statistical_exception_report": exception_report,
        "identity_crosscheck": identity_crosscheck,
        "team_validation_diagnostics_scope": "STAGED_SCHOOL_AGGREGATES_ONLY_NO_RAW_PROVIDER_ROWS",
        "staged_school_names_requiring_statistical_review": {k: sorted(unresolved_schools[k]) for k in actionable_reasons},
        "official_membership_source": "https://web3.ncaa.org/directory/memberList?division=I&sportCode=MBB&type=12",
        "official_membership_reconciliation": "PENDING_INDEPENDENT_SCHOOL_BY_SCHOOL_VERIFICATION",
        "sample_school_names_by_category": dict(sorted(examples.items())),
        "conference_roster_evidence": membership["counts"],
        "team_coverage": {"staged_teams_with_one_valid_team_record": sum(len(v) == 1 for v in team_games.values()), "staged_teams_with_at_least_five_games": sum(len(v) == 1 and v[0] >= MIN_GAMES for v in team_games.values())},
        "player_coverage": player_summary,
        "identity_and_coverage_diagnostics": dict(sorted(diagnostics.items())),
        "schedule_identity_crosscheck": "NOT_RUN_NO_SCHEDULE_REQUEST",
        "identity_crosscheck_method": "EXISTING_TEAM_AND_PLAYER_RECORDS_NO_ADDITIONAL_REQUESTS",
        "ncaa_sport_specific_membership": "NOT_INDEPENDENTLY_VERIFIED",
        "publication": "DISABLED",
        "note": "Statistical coverage is independent of five-game matchup ranking maturity. Neither implies eligibility or permission to publish. All schools require independent NCAA sport-specific verification before expansion."
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

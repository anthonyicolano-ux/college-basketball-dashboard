"""Manual, read-only player coverage validation for the approved private team scope.

One CBBD player-season request. Never logs or persists player records.
Publication is intentionally NOT implemented in this phase.
"""
import json
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from audit_bulk_candidate_matching import OFFICIAL_CONFERENCE_ROSTERS, PROVIDER_NAME_ALIASES, key
from transform_cbbd import player_row

SEASON = 2027
CORE = ('points','rebounds','offRebounds','defRebounds','assists','steals','blocks',
        'turnovers','fgMade','fgAttempted','threeMade','threeAttempted','ftMade','ftAttempted')


def approved_names():
    reference = json.loads(REFERENCE.read_text(encoding='utf-8'))
    candidates = json.loads(CANDIDATES.read_text(encoding='utf-8'))
    verified = validate_reference(reference)
    validate_candidates(candidates, verified)
    approved = {}
    for item in reference['schools']:
        approved[item['name']] = item
    for conference, roster in OFFICIAL_CONFERENCE_ROSTERS.items():
        expected = {key(n) for n in roster['schools']}
        matching = [x for x in candidates['candidates'] if x['conference'] == conference]
        existing = [x for x in reference['schools'] if x['conference'] == conference]
        combined_names = [x['name'] for x in (*existing, *matching)]
        combined_keys = [key(name) for name in combined_names]
        if len(combined_keys) != len(set(combined_keys)):
            raise ValueError('Duplicate official conference identity')
        if set(combined_keys) != expected:
            raise ValueError('Official conference roster mismatch')
        for item in matching:
            approved.setdefault(item['name'], item)
    lookup = {}
    for name, item in approved.items():
        for alias in (name, *item.get('aliases', []), *PROVIDER_NAME_ALIASES.get(name, ())):
            normalized = key(alias)
            if normalized in lookup and lookup[normalized] != name:
                raise ValueError('Ambiguous approved team alias')
            lookup[normalized] = name
    return lookup


def audit(records, lookup):
    if not isinstance(records, list):
        raise ValueError('Expected a list of player records')
    counts = Counter()
    seen = set()
    teams = set()
    coverage = Counter()
    for source in records:
        if not isinstance(source, dict) or source.get('season') != SEASON:
            counts['invalid_season_or_record'] += 1
            continue
        team = source.get('team')
        canonical = lookup.get(key(team)) if isinstance(team, str) else None
        if canonical is None:
            counts['outside_approved_scope'] += 1
            continue
        try:
            row = player_row(source)
            name = row['name'].strip()
            if row['games'] <= 0 or not name:
                raise ValueError('Missing games or player name')
            if any(row.get(k) is None for k in CORE):
                raise ValueError('Missing core player statistic')
            if abs(row['offRebounds'] + row['defRebounds'] - row['rebounds']) > 0.001:
                raise ValueError('Rebound totals disagree')
            for pct in ('fgPct', 'threePct', 'ftPct'):
                value = row.get(pct)
                if value is not None and not 0 <= value <= 100:
                    raise ValueError('Invalid shooting percentage')
            identity = (canonical.casefold(), name.casefold())
            if identity in seen:
                counts['duplicate_player_identity'] += 1
                continue
            seen.add(identity)
            teams.add(canonical)
            counts['validated_players'] += 1
            for field in CORE + ('fgPct','threePct','ftPct','minutes'):
                coverage[field] += row.get(field) is not None
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            counts['invalid_or_incomplete_player'] += 1
    if not counts['validated_players'] or not teams:
        raise ValueError('No valid player records for approved teams')
    return {
        'season': SEASON,
        'approved_teams_with_players': len(teams),
        'validated_players': counts['validated_players'],
        'excluded_counts': {k:v for k,v in sorted(counts.items()) if k != 'validated_players'},
        'field_coverage': dict(sorted(coverage.items())),
        'publication': 'DISABLED',
    }


def main():
    try:
        lookup = approved_names()
        token = os.environ.get('CBBD_API_KEY', '').strip()
        if not token:
            raise ValueError('Missing API credential')
        url = 'https://api.collegebasketballdata.com/stats/player/season?' + urlencode({
            'season': SEASON, 'seasonType': 'regular'
        })
        request = Request(url, headers={'Authorization':'Bearer ' + token, 'Accept':'application/json'})
        with urlopen(request, timeout=50) as response:
            records = json.load(response)
        result = audit(records, lookup)
        print('PRIVATE PLAYER COVERAGE: ' + json.dumps(result, sort_keys=True))
        print('DRY RUN: one CBBD request; no provider rows, KV writes, artifacts, or publication.')
        return 0
    except Exception as error:
        print('FAIL: private player validation; error_type=' + type(error).__name__ + '; no raw records or credentials printed.')
        return 1


if __name__ == '__main__':
    sys.exit(main())

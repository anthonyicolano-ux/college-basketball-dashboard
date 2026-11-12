"""Read-only reconciliation framework for 2026-27 D-I men's basketball.

Official NCAA sport-specific membership reference is required before classification.
Verified-reference entries and candidate staging entries are kept separate.
One CBBD request, aggregate logs only; never publishes data.
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from transform_cbbd import team_row

REFERENCE = Path(__file__).resolve().parents[1] / 'references' / 'di_mens_basketball_2026_27.json'
CANDIDATES = Path(__file__).resolve().parents[1] / 'references' / 'di_mens_basketball_candidates_2026_27.json'

def normalized(name):
    return ' '.join(name.casefold().strip().split())

def validate_reference(data):
    if data.get('season') != 2027 or data.get('sport') != 'mens_basketball':
        raise ValueError('Incorrect reference season or sport')
    baseline = data.get('official_baseline', {})
    if baseline.get('projected_mens_basketball_sponsorship') != 365 or baseline.get('primary_division_i_conferences') != 32:
        raise ValueError('Official NCAA baseline missing or inconsistent')
    entries = data.get('schools')
    if not isinstance(entries, list):
        raise ValueError('Reference schools must be a list')
    index = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('name'), str) or not entry['name'].strip():
            raise ValueError('Invalid reference entry')
        if entry.get('status') not in ('active', 'reclassifying'):
            raise ValueError('Unverified membership status')
        if not isinstance(entry.get('conference'), str) or not entry['conference'].strip():
            raise ValueError('Missing reference conference')
        if not isinstance(entry.get('source_url'), str) or not entry['source_url'].startswith('https://'):
            raise ValueError('Missing source citation')
        aliases = entry.get('aliases', [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            raise ValueError('Invalid aliases')
        for name in [entry['name'], *aliases]:
            key = normalized(name)
            if key in index:
                raise ValueError('Duplicate reference alias')
            index[key] = entry
    return index

def validate_candidates(data, verified_index):
    if data.get('season') != 2027 or data.get('sport') != 'mens_basketball':
        raise ValueError('Incorrect candidate reference season or sport')
    if data.get('status') != 'CANDIDATES_ONLY_NOT_ELIGIBILITY':
        raise ValueError('Candidate reference must be quarantined')
    entries = data.get('candidates')
    if not isinstance(entries, list):
        raise ValueError('Candidate entries must be a list')
    seen = set(verified_index)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid candidate entry')
        name = entry.get('name')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Candidate missing name')
        if entry.get('verification_status') not in ('pending', 'conflicting'):
            raise ValueError('Candidate must remain unverified')
        source = entry.get('source_url')
        if not isinstance(source, str) or not source.startswith('https://'):
            raise ValueError('Candidate missing source URL')
        conference = entry.get('conference')
        if conference is not None and (not isinstance(conference, str) or not conference.strip()):
            raise ValueError('Invalid candidate conference')
        aliases = entry.get('aliases', [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            raise ValueError('Invalid candidate aliases')
        for alias in [name, *aliases]:
            key = normalized(alias)
            if key in seen:
                raise ValueError('Duplicate or conflicting candidate alias')
            seen.add(key)
    return len(entries)

def audit(records, index):
    if not isinstance(records, list):
        raise ValueError('Provider response is not a list')
    counts = Counter()
    matched_schools = set()
    conference_disagreement = 0
    for record in records:
        if not isinstance(record, dict) or record.get('season') != 2027:
            continue
        counts['provider_records'] += 1
        name = record.get('team')
        if not isinstance(name, str) or not name.strip():
            counts['missing_provider_identity'] += 1
            continue
        member = index.get(normalized(name))
        if member is None:
            counts['not_verified_by_reference'] += 1
        else:
            counts['matched_reference_records'] += 1
            matched_schools.add(member['name'])
            if not record.get('conference'):
                counts['reference_can_fill_missing_conference'] += 1
            elif normalized(str(record['conference'])) != normalized(member['conference']):
                conference_disagreement += 1
        try:
            row = team_row(record)
            games, wins, losses = row.get('games'), row.get('wins'), row.get('losses')
            if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (games, wins, losses)):
                delta = games - wins - losses
                if delta > 0:
                    counts['games_greater_than_wins_plus_losses'] += 1
                    if delta == 1:
                        counts['gap_of_one'] += 1
                    else:
                        counts['gap_greater_than_one'] += 1
                elif delta < 0:
                    counts['wins_plus_losses_greater_than_games'] += 1
            else:
                counts['missing_game_count_fields'] += 1
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            counts['transformation_errors'] += 1
    return {
        'reference_schools': len({v['name'] for v in index.values()}),
        'ncaa_projected_sponsorship': 365,
        'reference_remaining_to_projection': max(0, 365 - len({v['name'] for v in index.values()})),
        'note': 'Projection is a benchmark, not proof of membership or eligibility',
        'reference_matches': len(matched_schools),
        'conference_disagreements': conference_disagreement,
        'counts': dict(sorted(counts.items())),
        'eligibility': 'UNVERIFIED' if not index else 'PARTIAL_REFERENCE_ONLY',
        'publication': 'DISABLED'
    }

def main():
    try:
        index = validate_reference(json.loads(REFERENCE.read_text(encoding='utf-8')))
        candidate_count = validate_candidates(json.loads(CANDIDATES.read_text(encoding='utf-8')), index)
    except (OSError, ValueError, TypeError):
        print('FAIL: invalid membership reference; no API request.')
        return 2
    token = os.environ.get('CBBD_API_KEY', '').strip()
    if not token:
        print('FAIL: API key missing; no request.')
        return 2
    try:
        url = 'https://api.collegebasketballdata.com/stats/team/season?' + urlencode({'season': 2027, 'seasonType': 'regular'})
        req = Request(url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
        with urlopen(req, timeout=40) as response:
            records = json.load(response)
        report = audit(records, index)
        report['staged_candidates'] = candidate_count
        report['candidate_publication'] = 'DISABLED'
        print('MEMBERSHIP RECONCILIATION: ' + json.dumps(report, sort_keys=True))
        print('DRY RUN: one API request; no raw records logged, KV writes, or publication.')
        return 0
    except Exception as error:
        print('FAIL: reconciliation (' + type(error).__name__ + '); no records or secrets printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

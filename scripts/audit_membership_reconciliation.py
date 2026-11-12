"""Read-only reconciliation framework for 2026-27 D-I men's basketball.

Official NCAA sport-specific membership reference is required before classification.
Reference JSON is intentionally empty until names and aliases are verified.
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

def normalized(name):
    return ' '.join(name.casefold().strip().split())

def validate_reference(data):
    if data.get('season') != 2027 or data.get('sport') != 'mens_basketball':
        raise ValueError('Incorrect reference season or sport')
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
        'reference_matches': len(matched_schools),
        'conference_disagreements': conference_disagreement,
        'counts': dict(sorted(counts.items())),
        'eligibility': 'UNVERIFIED' if not index else 'PARTIAL_REFERENCE_ONLY',
        'publication': 'DISABLED'
    }

def main():
    try:
        index = validate_reference(json.loads(REFERENCE.read_text(encoding='utf-8')))
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
        print('MEMBERSHIP RECONCILIATION: ' + json.dumps(audit(records, index), sort_keys=True))
        print('DRY RUN: one API request; no raw records logged, KV writes, or publication.')
        return 0
    except Exception as error:
        print('FAIL: reconciliation (' + type(error).__name__ + '); no records or secrets printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

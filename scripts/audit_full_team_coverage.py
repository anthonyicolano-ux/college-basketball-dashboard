"""Read-only full-season coverage audit; one CBBD request, no publishing.

Logs aggregate counts only. Never writes provider records or response bodies.
"""
import json
import math
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from transform_cbbd import team_row
from prepare_private_teams import REQUIRED

def audit(records):
    if not isinstance(records, list):
        raise ValueError('Response must be a list')
    selected = [r for r in records if isinstance(r, dict) and r.get('season') == 2027]
    if not selected:
        raise ValueError('No season records')
    seen = set()
    complete = 0
    incomplete = 0
    errors = 0
    conferences = set()
    reasons = Counter()
    for record in selected:
        name = record.get('team')
        if not isinstance(name, str) or not name.strip():
            reasons['missing_identity'] += 1
            incomplete += 1
            continue
        key = name.strip().casefold()
        if key in seen:
            reasons['duplicate_team'] += 1
            errors += 1
            continue
        seen.add(key)
        try:
            row = team_row(record)
            conference = row.get('conference')
            if isinstance(conference, str) and conference.strip():
                conferences.add(conference.strip().casefold())
            else:
                reasons['missing_conference'] += 1
            missing = [field for field in REQUIRED if row.get(field) is None]
            if not isinstance(row.get('games'), (int, float)) or row['games'] <= 0:
                reasons['no_completed_games'] += 1
                incomplete += 1
            elif missing or any(isinstance(v, float) and not math.isfinite(v) for v in row.values()):
                reasons['incomplete_metrics'] += 1
                incomplete += 1
            elif (row.get('wins') is None or row.get('losses') is None or
                  row['wins'] + row['losses'] != row['games']):
                reasons['record_inconsistent'] += 1
                errors += 1
            elif abs(row['offRating'] - row['defRating'] - row['netRating']) > 0.15 or abs(row['ppg'] - row['oppPpg'] - row['scoringMargin']) > 0.15:
                reasons['rating_inconsistent'] += 1
                errors += 1
            else:
                complete += 1
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            reasons['transform_error'] += 1
            errors += 1
    return dict(records=len(selected), unique_teams=len(seen), conferences=len(conferences),
                complete=complete, incomplete=incomplete, errors=errors,
                issues=dict(sorted(reasons.items())), publication='DISABLED')

def main():
    key = os.environ.get('CBBD_API_KEY', '').strip()
    if not key:
        print('FAIL: API key missing; no request made.')
        return 2
    try:
        url = 'https://api.collegebasketballdata.com/stats/team/season?' + urlencode({'season': 2027, 'seasonType': 'regular'})
        request = Request(url, headers={'Authorization': 'Bearer ' + key, 'Accept': 'application/json'})
        with urlopen(request, timeout=40) as response:
            records = json.load(response)
        print('COVERAGE AUDIT: ' + json.dumps(audit(records), sort_keys=True))
        print('DRY RUN: one CBBD request; no KV access, uploads, or stored records.')
        return 0
    except Exception as error:
        print('FAIL: coverage audit (' + type(error).__name__ + '); no provider data or credentials printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

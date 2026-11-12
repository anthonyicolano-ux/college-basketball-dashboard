"""Offline-only validation for a future multi-team private pilot.

No provider requests, no KV access, no publication. Accepts normalized rows
only and prints aggregate counts, never team-level provider records.
"""
import math

REQUIRED = ('team', 'conference', 'games', 'wins', 'losses', 'ppg',
            'oppPpg', 'offRating', 'defRating', 'netRating', 'scoringMargin')
NUMERIC = ('games', 'wins', 'losses', 'ppg', 'oppPpg',
           'offRating', 'defRating', 'netRating', 'scoringMargin')

def validate_rows(rows, min_teams=2, max_teams=12):
    if not isinstance(rows, list) or not min_teams <= len(rows) <= max_teams:
        raise ValueError('Pilot team count outside allowed range')
    names = set()
    conferences = set()
    for row in rows:
        if not isinstance(row, dict) or any(row.get(k) is None for k in REQUIRED):
            raise ValueError('Missing required team data')
        team = row['team']
        conference = row['conference']
        if not isinstance(team, str) or not team.strip() or not isinstance(conference, str) or not conference.strip():
            raise ValueError('Missing team or conference identity')
        key = team.strip().casefold()
        if key in names:
            raise ValueError('Duplicate team')
        names.add(key)
        conferences.add(conference.strip().casefold())
        for field in NUMERIC:
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Invalid numeric field')
        if row['games'] <= 0 or row['wins'] < 0 or row['losses'] < 0 or row['wins'] + row['losses'] != row['games']:
            raise ValueError('Inconsistent record')
        if abs((row['offRating'] - row['defRating']) - row['netRating']) > 0.15:
            raise ValueError('Net rating mismatch')
        if abs((row['ppg'] - row['oppPpg']) - row['scoringMargin']) > 0.15:
            raise ValueError('Scoring margin mismatch')
    if len(conferences) < 2:
        raise ValueError('Pilot must cover at least two conferences')
    return {'teams': len(names), 'conferences': len(conferences), 'publication': 'DISABLED'}

if __name__ == '__main__':
    import json
    from pathlib import Path
    import sys
    if len(sys.argv) != 2:
        print('Usage: python scripts/validate_multi_team_pilot.py /path/to/normalized-rows.json')
        sys.exit(2)
    try:
        rows = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        print(json.dumps(validate_rows(rows)))
    except (ValueError, OSError, TypeError, KeyError):
        print('FAIL: offline multi-team validation (details withheld).')
        sys.exit(1)

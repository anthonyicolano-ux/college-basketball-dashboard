"""Read-only four-team CBBD pilot: one season request, zero publication.

Only aggregate validation results are logged; provider records remain in memory.
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from prepare_private_teams import prepare
from validate_multi_team_pilot import validate_rows

# Provider naming varies for Connecticut; accept either name, never guess.
TARGETS = {
    'Duke': {'duke'},
    'Kansas': {'kansas'},
    'UConn': {'uconn', 'connecticut'},
    'Gonzaga': {'gonzaga'},
}
EXPECTED_CONFERENCES = {
    'Duke': {'acc'},
    'Kansas': {'big 12', 'big 12 conference'},
    'UConn': {'big east', 'big east conference'},
    'Gonzaga': {'wcc', 'west coast', 'west coast conference'},
}

def choose(records):
    selected = {}
    for record in records:
        if not isinstance(record, dict) or record.get('season') != 2027:
            continue
        name = record.get('team')
        if not isinstance(name, str):
            continue
        for target, aliases in TARGETS.items():
            if name.strip().casefold() in aliases:
                if target in selected:
                    raise ValueError('Duplicate target team record')
                selected[target] = record
    if set(selected) != set(TARGETS):
        raise ValueError('Missing one or more requested teams')
    return selected

def main():
    if not os.environ.get('CBBD_API_KEY', '').strip():
        print('FAIL: missing CBBD_API_KEY; no API request.')
        return 2
    stage = 'API request or response'
    try:
        url = 'https://api.collegebasketballdata.com/stats/team/season?' + urlencode({
            'season': 2027, 'seasonType': 'regular'})
        req = Request(url, headers={
            'Authorization': 'Bearer ' + os.environ['CBBD_API_KEY'].strip(),
            'Accept': 'application/json'})
        with urlopen(req, timeout=35) as response:
            records = json.load(response)
        if not isinstance(records, list):
            raise ValueError('Unexpected API response')
        stage = 'target team selection'
        selected = choose(records)
        stage = 'team statistics transformation and completeness'
        dataset = prepare(list(selected.values()))
        rows = dataset['rows']
        stage = 'conference verification'
        for target, aliases in TARGETS.items():
            row = next((r for r in rows if r['team'].strip().casefold() in aliases), None)
            if row is None:
                print('DIAGNOSTIC: team=' + target + '; reason=missing transformed row')
                raise ValueError('Missing transformed team')
            conference = row.get('conference')
            if not isinstance(conference, str) or not conference.strip():
                print('DIAGNOSTIC: team=' + target + '; reason=missing conference')
                raise ValueError('Missing conference')
            if conference.strip().casefold() not in EXPECTED_CONFERENCES[target]:
                # Conference labels are public metadata, but sanitize before logging.
                # No provider statistics, raw records, or credentials are printed.
                safe_label = ''.join(ch for ch in conference[:80] if ch.isalnum() or ch in ' -_&.()/')
                print('DIAGNOSTIC: team=' + target +
                      '; reason=unexpected conference label; observed=' + repr(safe_label))
                raise ValueError('Unexpected conference label')
        stage = 'cross-team metric and record consistency'
        summary = validate_rows(rows, min_teams=4, max_teams=4)
        print('PASS: real four-team pilot validated; teams=4; conferences=' +
              str(summary['conferences']) + '; CBBD requests=1.')
        print('DRY RUN: no Cloudflare access, KV writes, GitHub artifacts, or data publication.')
        return 0
    except Exception as error:
        print('FAIL: stage=' + stage + '; error_type=' + type(error).__name__ +
              '; no provider records, response bodies, or credentials printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

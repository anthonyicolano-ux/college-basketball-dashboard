"""One-request, read-only audit of D-I identification and conference field coverage.

This does NOT infer NCAA D-I eligibility from team counts or conferences.
Only aggregate counts and field names are printed; no team names or raw records.
"""
import json
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from transform_cbbd import team_row

def audit(records):
    if not isinstance(records, list):
        raise ValueError('Expected list')
    season = [r for r in records if isinstance(r, dict) and r.get('season') == 2027]
    if not season:
        raise ValueError('No 2027 records')
    result = Counter()
    missing_conference_keys = Counter()
    alternative_fields = Counter()
    mismatches = Counter()
    unique = set()
    for record in season:
        name = record.get('team')
        if not isinstance(name, str) or not name.strip():
            result['missing_team_identity'] += 1
            continue
        identity = name.strip().casefold()
        if identity in unique:
            result['duplicate_team_records'] += 1
            continue
        unique.add(identity)
        conference = record.get('conference')
        if not isinstance(conference, str) or not conference.strip():
            result['missing_conference'] += 1
            # Report only approved generic field names, never their values.
            for field in ('conferenceName', 'conferenceId', 'conferenceAbbreviation',
                          'conferenceShortName', 'teamConference', 'division',
                          'classification', 'isDivisionOne', 'isDivisionI'):
                if record.get(field) is not None:
                    alternative_fields[field] += 1
            for field in ('conference', 'conferenceName', 'conferenceId',
                          'conferenceAbbreviation', 'conferenceShortName'):
                if field not in record:
                    missing_conference_keys[field] += 1
        try:
            row = team_row(record)
            wins, losses, games = row.get('wins'), row.get('losses'), row.get('games')
            if all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in (wins, losses, games)):
                if wins + losses != games:
                    result['wins_losses_not_equal_games'] += 1
                    # Diagnose counts only; do not alter any stats.
                    if wins + losses < games:
                        mismatches['wins_plus_losses_below_games'] += 1
                    else:
                        mismatches['wins_plus_losses_above_games'] += 1
            else:
                result['missing_record_fields'] += 1
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            result['transformation_errors'] += 1
    return {
        'season': 2027,
        'records': len(season),
        'unique_named_teams': len(unique),
        'missing_conference': result['missing_conference'],
        'alternative_conference_or_eligibility_field_presence': dict(sorted(alternative_fields.items())),
        'conference_keys_absent_on_missing_records': dict(sorted(missing_conference_keys.items())),
        'record_inconsistency': dict(sorted(mismatches.items())),
        'other_issues': {k: result[k] for k in ('duplicate_team_records',
            'missing_team_identity', 'missing_record_fields', 'transformation_errors')},
        'division_one_eligibility': 'UNVERIFIED: authoritative D-I membership roster required',
        'publication': 'DISABLED'
    }

def main():
    token = os.environ.get('CBBD_API_KEY', '').strip()
    if not token:
        print('FAIL: API key missing; no request made.')
        return 2
    try:
        url = 'https://api.collegebasketballdata.com/stats/team/season?' + urlencode(
            {'season': 2027, 'seasonType': 'regular'})
        request = Request(url, headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'})
        with urlopen(request, timeout=40) as response:
            records = json.load(response)
        print('ELIGIBILITY AUDIT: ' + json.dumps(audit(records), sort_keys=True))
        print('DRY RUN: one CBBD request; no KV access, uploads, or stored records.')
        return 0
    except Exception as error:
        print('FAIL: eligibility audit (' + type(error).__name__ + '); no records or secrets printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

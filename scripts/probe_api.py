"""Private, read-only CBBD field/entitlement probe. Never prints or stores raw records."""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://api.collegebasketballdata.com'
SEASON = 2027
TEAM = 'Duke'
ENDPOINTS = ('/stats/team/season', '/stats/player/season', '/games')

def field_paths(value, prefix=''):
    if not isinstance(value, dict):
        return []
    out = []
    for key, item in value.items():
        path = f'{prefix}.{key}' if prefix else key
        if isinstance(item, dict):
            out.extend(field_paths(item, path))
        else:
            out.append((path, item))
    return out

def summarize(records):
    if not isinstance(records, list):
        return {'error': 'Unexpected response type (expected array)'}
    if not records:
        return {'record_count': 0, 'note': 'No records; cannot verify fields'}
    paths = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        for path, val in field_paths(record):
            stat = paths.setdefault(path, {'present': 0, 'null': 0})
            stat['present'] += 1
            stat['null'] += val is None
    return {'record_count': len(records), 'fields': paths}

def probe(key, endpoint):
    url = BASE + endpoint + '?' + urlencode({'season': SEASON, 'team': TEAM})
    request = Request(url, headers={'Authorization': f'Bearer {key}', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
        return {'status': 200, **summarize(payload)}
    except HTTPError as error:
        # Don't print response body; it could contain sensitive details.
        return {'status': error.code, 'note': 'Authentication, entitlement, quota or request error; consult provider documentation'}
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return {'status': 'connection_or_format_error'}

def main():
    key = os.environ.get('CBBD_API_KEY', '').strip()
    if not key:
        print('CBBD_API_KEY not configured. No requests made.')
        return 2
    print(f'Private field check: season={SEASON}, team={TEAM}; at most {len(ENDPOINTS)} requests')
    for endpoint in ENDPOINTS:
        result = probe(key, endpoint)
        print('\n' + endpoint)
        print(json.dumps(result, indent=2, sort_keys=True))
    print('\nNo raw API responses, player names, or credentials saved or printed.')
    return 0

if __name__ == '__main__':
    sys.exit(main())

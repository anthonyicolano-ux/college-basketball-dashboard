"""Manual, private CBBD team refresh dry run. One API request; no publication.

The script retrieves one team's season record, validates the complete dashboard
contract in memory, and prints aggregate diagnostics only. It never saves raw
records or sends data to Cloudflare.
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from prepare_private_teams import prepare

BASE = 'https://api.collegebasketballdata.com/stats/team/season'
SEASON = 2027
TEAM = 'Duke'

def main():
    key = os.environ.get('CBBD_API_KEY', '').strip()
    if not key:
        print('FAIL: CBBD_API_KEY missing; zero requests made.')
        return 2
    url = BASE + '?' + urlencode({'season': SEASON, 'team': TEAM})
    request = Request(url, headers={
        'Authorization': 'Bearer ' + key,
        'Accept': 'application/json',
    })
    try:
        with urlopen(request, timeout=25) as response:
            records = json.load(response)
        if not isinstance(records, list) or len(records) != 1:
            raise ValueError('Expected exactly one team record')
        dataset = prepare(records)
        if dataset['rows'][0]['team'].casefold() != TEAM.casefold():
            raise ValueError('Unexpected team identity')
        print(json.dumps({
            'result': 'PASS',
            'season': SEASON,
            'team_count': len(dataset['rows']),
            'complete_team_rows': len(dataset['rows']),
            'publication': 'DISABLED',
            'api_requests': 1,
        }))
        return 0
    except Exception as error:
        print('FAIL: private team refresh validation (' +
              type(error).__name__ + '); no records published.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

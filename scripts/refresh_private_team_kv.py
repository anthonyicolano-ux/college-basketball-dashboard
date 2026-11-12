"""One-request manual CBBD team refresh with opt-in private KV publication.

Default: validate only. No raw provider records, outputs, or artifacts are
committed to GitHub. Publication requires explicit rights attestation.
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from prepare_private_teams import prepare

SEASON = 2027
TEAM = 'Duke'
KV_NAMESPACE = '7f0ff2851f7044c9b09c5c181f5d499b'
KV_KEY = 'teams'

def main():
    publish = os.environ.get('PUBLISH_PRIVATE_KV') == 'true'
    approval = os.environ.get('PUBLICATION_APPROVAL', '')
    if publish and approval != 'I CONFIRM PRIVATE DATA DISPLAY IS PERMITTED':
        print('BLOCKED: explicit provider-rights approval missing; zero requests.')
        return 2
    api_key = os.environ.get('CBBD_API_KEY', '').strip()
    if not api_key:
        print('BLOCKED: missing CBBD_API_KEY; zero requests.')
        return 2
    if publish:
        account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '').strip()
        token = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
        if not account or not token or not all(c in '0123456789abcdefABCDEF' for c in account):
            print('BLOCKED: Cloudflare credentials missing or account ID invalid; zero requests.')
            return 2
    try:
        query = urlencode({'season': SEASON, 'team': TEAM})
        req = Request('https://api.collegebasketballdata.com/stats/team/season?' + query,
                      headers={'Authorization': 'Bearer ' + api_key, 'Accept': 'application/json'})
        with urlopen(req, timeout=25) as response:
            records = json.load(response)
        if not isinstance(records, list) or len(records) != 1:
            raise ValueError('Expected exactly one team')
        dataset = prepare(records)
        if dataset['rows'][0]['team'].casefold() != TEAM.casefold():
            raise ValueError('Wrong team')
        print('PASS: one team validated; one CBBD request; no raw records logged.')
        if not publish:
            print('DRY RUN: KV publication disabled.')
            return 0
        payload = json.dumps(dataset, ensure_ascii=False, allow_nan=False).encode('utf-8')
        kv_url = ('https://api.cloudflare.com/client/v4/accounts/' + account +
                  '/storage/kv/namespaces/' + KV_NAMESPACE + '/values/' + KV_KEY)
        put = Request(kv_url, data=payload, method='PUT', headers={
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json',
        })
        with urlopen(put, timeout=25) as response:
            result = json.load(response)
        if result.get('success') is not True:
            raise ValueError('KV write not confirmed')
        print('PASS: private KV key teams updated; one team only.')
        return 0
    except Exception as error:
        print('FAIL: refresh or KV operation (' + type(error).__name__ +
              '); no sensitive payload printed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

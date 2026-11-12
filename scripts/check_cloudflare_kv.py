"""Read-only Cloudflare KV credential and namespace connectivity check.

No CBBD requests, no KV writes/deletes, and no secrets in logs.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NAMESPACE = '7f0ff2851f7044c9b09c5c181f5d499b'

def main():
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID', '').strip()
    token = os.environ.get('CLOUDFLARE_API_TOKEN', '').strip()
    if len(account) != 32 or any(c not in '0123456789abcdefABCDEF' for c in account) or not token:
        print('FAIL: missing or malformed Cloudflare configuration; zero network requests.')
        return 2
    url = ('https://api.cloudflare.com/client/v4/accounts/' + account +
           '/storage/kv/namespaces/' + NAMESPACE)
    req = Request(url, headers={'Authorization': 'Bearer ' + token,
                                'Accept': 'application/json'}, method='GET')
    try:
        with urlopen(req, timeout=20) as response:
            payload = json.load(response)
        if payload.get('success') is not True:
            print('FAIL: Cloudflare did not confirm namespace access.')
            return 1
        result = payload.get('result') or {}
        if result.get('id') != NAMESPACE:
            print('FAIL: Cloudflare returned an unexpected KV namespace.')
            return 1
        print('PASS: Cloudflare authenticated; expected KV namespace accessible (read-only).')
        print('No basketball API requests, KV writes, or deletes performed.')
        return 0
    except HTTPError as error:
        print('FAIL: Cloudflare returned HTTP ' + str(error.code) +
              '. A write-only token may not authorize this read-only check.')
        return 1
    except (URLError, ValueError, OSError, TypeError):
        print('FAIL: Cloudflare read-only check could not be completed.')
        return 1

if __name__ == '__main__':
    sys.exit(main())

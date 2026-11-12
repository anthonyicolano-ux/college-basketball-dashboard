"""Manual four-team private pilot; one provider request, opt-in KV upload."""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dry_run_real_multi_team import choose, TARGETS, EXPECTED_CONFERENCES
from prepare_private_teams import prepare
from validate_multi_team_pilot import validate_rows

KV_NAMESPACE='7f0ff2851f7044c9b09c5c181f5d499b'

def main():
    publish=os.environ.get('PUBLISH_FOUR_TEAM_KV')=='true'
    if publish and os.environ.get('PUBLICATION_APPROVAL')!='I CONFIRM PRIVATE DATA DISPLAY IS PERMITTED':
        print('BLOCKED: publication approval missing; zero requests.')
        return 2
    api_key=os.environ.get('CBBD_API_KEY','').strip()
    account=os.environ.get('CLOUDFLARE_ACCOUNT_ID','').strip()
    token=os.environ.get('CLOUDFLARE_API_TOKEN','').strip()
    if not api_key or (publish and (len(account)!=32 or any(c not in '0123456789abcdefABCDEF' for c in account) or not token)):
        print('BLOCKED: required credentials missing or malformed; zero requests.')
        return 2
    stage='provider request'
    try:
        req=Request('https://api.collegebasketballdata.com/stats/team/season?'+urlencode({'season':2027,'seasonType':'regular'}),headers={'Authorization':'Bearer '+api_key,'Accept':'application/json'})
        with urlopen(req,timeout=35) as response:
            records=json.load(response)
        stage='team selection and transformation'
        selected=choose(records)
        dataset=prepare(list(selected.values()))
        rows=dataset['rows']
        stage='conference and metric validation'
        for target,aliases in TARGETS.items():
            row=next((r for r in rows if r['team'].strip().casefold() in aliases),None)
            if row is None or not isinstance(row.get('conference'),str) or row['conference'].strip().casefold() not in EXPECTED_CONFERENCES[target]:
                raise ValueError('Unexpected team conference')
        summary=validate_rows(rows,min_teams=4,max_teams=4)
        print('PASS: four real teams validated across '+str(summary['conferences'])+' conferences; one CBBD request.')
        if not publish:
            print('DRY RUN: KV publication disabled.')
            return 0
        stage='private KV publication'
        payload=json.dumps(dataset,ensure_ascii=False,allow_nan=False).encode('utf-8')
        url='https://api.cloudflare.com/client/v4/accounts/'+account+'/storage/kv/namespaces/'+KV_NAMESPACE+'/values/teams'
        put=Request(url,data=payload,method='PUT',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with urlopen(put,timeout=25) as response:
            result=json.load(response)
        if result.get('success') is not True:
            raise ValueError('KV write not confirmed')
        print('PASS: four-team private KV pilot published; no raw records logged.')
        return 0
    except Exception as error:
        print('FAIL: stage='+stage+'; type='+type(error).__name__+'; no provider records or credentials logged.')
        return 1

if __name__=='__main__':
    sys.exit(main())

"""One-request, approval-gated private 2026-27 schedule publishing."""
import json, os, sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dry_run_private_players import approved_names
from audit_bulk_candidate_matching import key

SEASON=2027
NAMESPACE="7f0ff2851f7044c9b09c5c181f5d499b"
APPROVAL="I APPROVE PRIVATE MATCHUP KV PUBLICATION"

def normalize(records, lookup):
    if not isinstance(records,list): raise ValueError("Invalid schedule response")
    rows=[]; seen=set(); excluded=0
    for g in records:
        if not isinstance(g,dict) or g.get("status")!="scheduled": continue
        home=g.get("homeTeam"); away=g.get("awayTeam")
        if not isinstance(home,str) or not isinstance(away,str) or home==away: continue
        h=lookup.get(key(home)); a=lookup.get(key(away))
        if not h and not a:
            excluded+=1; continue
        dt=g.get("startDate")
        if not isinstance(dt,str) or not dt.endswith("Z"): continue
        try: start=datetime.fromisoformat(dt.replace("Z","+00:00"))
        except ValueError: continue
        if start < datetime.now(timezone.utc): continue
        gid=str(g.get("id",g.get("gameId","")))
        if not gid or gid in seen: continue
        seen.add(gid)
        rows.append({"gameId":gid,"startDate":dt,"homeTeam":h or home,"awayTeam":a or away,
                     "homeCovered":bool(h),"awayCovered":bool(a),
                     "startTimeTbd":g.get("startTimeTbd") is True,
                     "neutralSite":g.get("neutralSite") is True,"status":"scheduled"})
    rows.sort(key=lambda r:(r["startDate"],r["gameId"]))
    if not rows: raise ValueError("No upcoming games for approved teams")
    if len(rows)>1200: raise ValueError("Unexpected schedule size")
    return rows,excluded

def main():
    publish=os.getenv("PUBLISH_PRIVATE_MATCHUPS")=="true"
    if publish and os.getenv("PUBLICATION_APPROVAL")!=APPROVAL:
        print("BLOCKED: exact approval required; no API request.");return 2
    token=os.getenv("CBBD_API_KEY","").strip()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    cf=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if not token or (publish and (len(account)!=32 or not all(c in "0123456789abcdefABCDEF" for c in account) or not cf)):
        print("BLOCKED: missing credentials; no API request.");return 2
    stage="schedule request"
    try:
        lookup=approved_names()
        url="https://api.collegebasketballdata.com/games?"+urlencode({"season":SEASON})
        with urlopen(Request(url,headers={"Authorization":"Bearer "+token,"Accept":"application/json"}),timeout=60) as response:
            source=json.load(response)
        stage="schedule validation"
        rows,excluded=normalize(source,lookup)
        payload=json.dumps({"schemaVersion":1,"season":SEASON,"demo":False,
                            "generatedAt":datetime.now(timezone.utc).isoformat(),"rows":rows},
                           ensure_ascii=False,allow_nan=False).encode()
        if len(payload)>1000000:raise ValueError("Schedule exceeds size cap")
        print("PASS: upcoming approved-scope games="+str(len(rows))+"; excluded other games="+str(excluded)+"; bytes="+str(len(payload))+".")
        if not publish:
            print("DRY RUN: one CBBD request; no KV writes, records logged, or publication.");return 0
        stage="private KV publication"
        endpoint="https://api.cloudflare.com/client/v4/accounts/"+account+"/storage/kv/namespaces/"+NAMESPACE+"/values/schedule"
        with urlopen(Request(endpoint,data=payload,method="PUT",headers={"Authorization":"Bearer "+cf,"Content-Type":"application/json"}),timeout=30) as response:
            result=json.load(response)
        if result.get("success") is not True:raise ValueError("KV write not confirmed")
        print("PASS: private schedule published to KV schedule key; no raw records logged.");return 0
    except Exception as e:
        print("FAIL: stage="+stage+"; error_type="+type(e).__name__+"; no provider records or credentials printed.");return 1

if __name__=="__main__":sys.exit(main())

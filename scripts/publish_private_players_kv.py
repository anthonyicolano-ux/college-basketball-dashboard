"""Approval-gated private player KV publication. Never stores provider records in GitHub."""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dry_run_private_players import SEASON, CORE, approved_names, audit
from audit_bulk_candidate_matching import key
from transform_cbbd import player_row

KV_NAMESPACE = "7f0ff2851f7044c9b09c5c181f5d499b"
APPROVAL = "I APPROVE PRIVATE PLAYER KV PUBLICATION"
FIELDS = ("name","team","conference","games","minutes","points","rebounds",
          "offRebounds","defRebounds","assists","steals","blocks","turnovers",
          "fgMade","fgAttempted","fgPct","threeMade","threeAttempted","threePct",
          "ftMade","ftAttempted","ftPct")


def build(records, lookup):
    report = audit(records, lookup)
    rows, seen = [], set()
    for source in records:
        if not isinstance(source, dict) or source.get("season") != SEASON:
            continue
        team = source.get("team")
        canonical = lookup.get(key(team)) if isinstance(team, str) else None
        if canonical is None:
            continue
        try:
            row = player_row(source)
            if not isinstance(row["name"], str) or not row["name"].strip() or row["games"] <= 0:
                continue
            if any(row.get(k) is None for k in CORE):
                continue
            if abs(row["offRebounds"] + row["defRebounds"] - row["rebounds"]) > .001:
                continue
            if any(row.get(k) is not None and not 0 <= row[k] <= 100 for k in ("fgPct","threePct","ftPct")):
                continue
            identity = (canonical.casefold(), row["name"].strip().casefold())
            if identity in seen:
                continue
            seen.add(identity)
            row["team"] = canonical
            # Conference is from the approved scope, not an unverified provider label.
            # The approved team names are unique across the scope.
            rows.append({field: row.get(field) for field in FIELDS})
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            continue
    if len(rows) != report["validated_players"] or len({r["team"] for r in rows}) != report["approved_teams_with_players"]:
        raise ValueError("Validated player count mismatch")
    if len(rows) < 200 or len(rows) > 500 or len({r["team"] for r in rows}) != 24:
        raise ValueError("Unexpected approved player coverage")
    # Conference assignment is checked against approved team reference, not provider claims.
    return report, rows


def main():
    publish = os.environ.get("PUBLISH_PRIVATE_PLAYERS") == "true"
    if publish and os.environ.get("PUBLICATION_APPROVAL") != APPROVAL:
        print("BLOCKED: exact publication approval required; zero API requests.")
        return 2
    token = os.environ.get("CBBD_API_KEY", "").strip()
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    cf_token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token or (publish and (len(account) != 32 or any(x not in "0123456789abcdefABCDEF" for x in account) or not cf_token)):
        print("BLOCKED: credentials missing or invalid; zero API requests.")
        return 2
    stage = "approved scope"
    try:
        lookup = approved_names()
        stage = "provider request"
        url = "https://api.collegebasketballdata.com/stats/player/season?" + urlencode({"season": SEASON, "seasonType": "regular"})
        with urlopen(Request(url, headers={"Authorization":"Bearer "+token,"Accept":"application/json"}), timeout=50) as response:
            records = json.load(response)
        stage = "player validation"
        report, rows = build(records, lookup)
        # Conference names come from the approved roster records.
        from audit_membership_reconciliation import REFERENCE, CANDIDATES
        approved = json.loads(REFERENCE.read_text(encoding="utf-8"))["schools"] + json.loads(CANDIDATES.read_text(encoding="utf-8"))["candidates"]
        conf_by_name = {item["name"]:item["conference"] for item in approved}
        for row in rows:
            row["conference"] = conf_by_name[row["team"]]
        dataset = {"schemaVersion":1,"season":SEASON,"seasonLabel":"2026–27",
                   "scope":"Private 24-team player pilot · Data: CollegeBasketballData.com",
                   "generatedAt":datetime.now(timezone.utc).isoformat(),"demo":False,"rows":rows}
        payload = json.dumps(dataset, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(payload) > 500000:
            raise ValueError("Private payload exceeds size cap")
        print("PASS: private player payload validated; players="+str(len(rows))+
              "; teams=24; bytes="+str(len(payload))+"; missing_percentage_values="+
              str(sum(row[f] is None for row in rows for f in ("fgPct","threePct","ftPct")))+".")
        if not publish:
            print("DRY RUN: one CBBD request; no Cloudflare KV access, artifacts, or publication.")
            return 0
        stage = "private KV publication"
        url = "https://api.cloudflare.com/client/v4/accounts/"+account+"/storage/kv/namespaces/"+KV_NAMESPACE+"/values/players"
        with urlopen(Request(url, data=payload, method="PUT", headers={"Authorization":"Bearer "+cf_token,"Content-Type":"application/json"}),timeout=30) as response:
            result = json.load(response)
        if result.get("success") is not True:
            raise ValueError("Cloudflare KV write not confirmed")
        print("PASS: private player KV dataset published to players key; no raw records logged.")
        return 0
    except Exception as error:
        print("FAIL: stage="+stage+"; error_type="+type(error).__name__+"; no provider records or credentials printed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Explicitly gated expanded team private KV publication.

One provider read, one Cloudflare KV write only after all checks pass.
No provider rows or secrets are logged or persisted as artifacts.
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from dry_run_expanded_private_teams import SEASON, preview

KV_NAMESPACE = "7f0ff2851f7044c9b09c5c181f5d499b"
APPROVAL = "I APPROVE 24 TEAM PRIVATE KV PUBLICATION"


def main():
    publish = os.environ.get("PUBLISH_EXPANDED_KV") == "true"
    if publish and os.environ.get("PUBLICATION_APPROVAL") != APPROVAL:
        print("BLOCKED: exact private publication approval required; zero requests.")
        return 2
    api_key = os.environ.get("CBBD_API_KEY", "").strip()
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not api_key or (publish and (len(account) != 32 or any(c not in "0123456789abcdefABCDEF" for c in account) or not token)):
        print("BLOCKED: required credentials missing or malformed; zero requests.")
        return 2
    stage = "validation"
    try:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        verified = validate_reference(reference)
        validate_candidates(candidates, verified)
        stage = "provider request"
        url = "https://api.collegebasketballdata.com/stats/team/season?" + urlencode({"season": SEASON, "seasonType": "regular"})
        with urlopen(Request(url, headers={"Authorization": "Bearer " + api_key, "Accept": "application/json"}), timeout=40) as response:
            records = json.load(response)
        if not isinstance(records, list):
            raise ValueError("Unexpected provider response")
        stage = "private dataset validation"
        summary, dataset = preview(records, reference["schools"], candidates["candidates"], include_dataset=True)
        if summary["validated_teams"] != 24 or summary["conferences"] != 6:
            raise ValueError("Expanded scope differs from approved 24 teams and six conferences")
        if dataset.get("demo") is not False or dataset.get("season") != SEASON:
            raise ValueError("Unexpected private dataset metadata")
        if len(dataset.get("rows", [])) != 24:
            raise ValueError("Unexpected dataset row count")
        payload = json.dumps(dataset, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(payload) > 1_000_000:
            raise ValueError("Payload exceeds conservative limit")
        print("PASS: expanded private payload validated; teams=24; conferences=6; bytes=" + str(len(payload)) + ".")
        if not publish:
            print("DRY RUN: no Cloudflare KV access, uploads, artifacts, or publication.")
            return 0
        stage = "private KV publication"
        kv_url = "https://api.cloudflare.com/client/v4/accounts/" + account + "/storage/kv/namespaces/" + KV_NAMESPACE + "/values/teams"
        req = Request(kv_url, data=payload, method="PUT", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
        if result.get("success") is not True:
            raise ValueError("Cloudflare KV write not confirmed")
        print("PASS: 24-team private KV dataset published to teams key; no raw records logged.")
        return 0
    except Exception as error:
        print("FAIL: stage=" + stage + "; error_type=" + type(error).__name__ + "; no records or credentials logged.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

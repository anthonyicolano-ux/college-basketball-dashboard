"""Stage an expanded private KV payload in memory; publication deliberately disabled.

One provider request. Never log raw provider records or write artifacts.
"""
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from audit_membership_reconciliation import REFERENCE, CANDIDATES, validate_reference, validate_candidates
from dry_run_expanded_private_teams import SEASON, preview

def main():
    if os.environ.get("PUBLISH_EXPANDED_KV", "").lower() == "true":
        print("BLOCKED: expanded publication is not enabled in this workflow; zero requests.")
        return 2
    token = os.environ.get("CBBD_API_KEY", "").strip()
    if not token:
        print("BLOCKED: CBBD_API_KEY missing; zero requests.")
        return 2
    try:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        verified = validate_reference(reference)
        validate_candidates(candidates, verified)
        url = "https://api.collegebasketballdata.com/stats/team/season?" + urlencode({"season": SEASON, "seasonType": "regular"})
        with urlopen(Request(url, headers={"Authorization": "Bearer " + token, "Accept": "application/json"}), timeout=40) as response:
            records = json.load(response)
        if not isinstance(records, list):
            raise ValueError("Unexpected provider response")
        summary, dataset = preview(records, reference["schools"], candidates["candidates"], include_dataset=True)
        if dataset["demo"] is not False or dataset["season"] != SEASON:
            raise ValueError("Invalid private payload metadata")
        if len(dataset["rows"]) != summary["validated_teams"]:
            raise ValueError("Private payload count mismatch")
        payload = json.dumps(dataset, ensure_ascii=False, allow_nan=False).encode("utf-8")
        if len(payload) > 1_000_000:
            raise ValueError("Payload exceeds conservative size limit")
        print("PASS: expanded private KV payload staged in memory; teams=" + str(summary["validated_teams"]) +
              "; conferences=" + str(summary["conferences"]) + "; payload_bytes=" + str(len(payload)) + ".")
        print("DRY RUN: one CBBD request; no KV credentials, writes, artifacts, records or publication.")
        return 0
    except Exception as error:
        print("FAIL: expanded private staging; error_type=" + type(error).__name__ + "; no records or credentials printed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

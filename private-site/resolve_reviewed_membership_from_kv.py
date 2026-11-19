"""Resolve independently reviewed school names against the PRIVATE KV candidate ID map.

Candidate identity matching is not NCAA membership approval. The reviewed names
must come from a separate official 2026-27 membership review. Never print IDs.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def resolve(mapping, reviewed):
    if mapping.get("season") != 2027 or mapping.get("reviewed") is not False or mapping.get("status") != "candidate_identity_only_not_division_one_approved":
        raise ValueError("Expected unapproved 2027 candidate identity map")
    names = mapping.get("teamIdsByName")
    if not isinstance(names, dict) or len(names) < 300:
        raise ValueError("Candidate identity map incomplete")
    if reviewed.get("season") != 2027 or reviewed.get("reviewed") is not True or reviewed.get("sport") != "mens_basketball":
        raise ValueError("Independent 2027 men's basketball membership approval required")
    approved = reviewed.get("schoolNames")
    if not isinstance(approved, list) or not 300 <= len(approved) <= 400 or len(set(approved)) != len(approved):
        raise ValueError("Approved school names invalid")
    missing = set(approved) - names.keys()
    if missing:
        raise ValueError(f"{len(missing)} reviewed schools missing from private candidate mapping")
    ids = [str(names[name]) for name in approved]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate provider IDs in reviewed membership")
    return {"season": 2027, "reviewed": True, "teamIds": ids}


def read_mapping():
    account, namespace, token = (os.environ.get(k) for k in
        ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_KV_NAMESPACE_ID", "CLOUDFLARE_API_TOKEN"))
    if not all((account, namespace, token)):
        raise ValueError("Missing private Cloudflare credentials")
    url = ("https://api.cloudflare.com/client/v4/accounts/" + quote(account,safe="") +
           "/storage/kv/namespaces/" + quote(namespace,safe="") +
           "/values/" + quote("basketball:candidate-team-ids:2027",safe=""))
    request = Request(url, headers={"Authorization":"Bearer "+token})
    with urlopen(request,timeout=30) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviewed-schools", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite membership file")
    reviewed = json.loads(args.reviewed_schools.read_text(encoding="utf-8"))
    result = resolve(read_mapping(), reviewed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result),encoding="utf-8")
    print(f"Resolved {len(result['teamIds'])} independently reviewed schools against private provider IDs")


if __name__ == "__main__":
    main()

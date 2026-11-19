"""Publish validated private basketball JSON to Cloudflare KV.

Default is offline dry-run. Publication requires explicit --publish and secrets.
Uses versioned keys, then changes a single active-release pointer only after
both uploads succeed. The Worker must support this pointer before activation.
Never print tokens or payloads, and never store raw provider responses here.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from prepare_private_release import release_manifest

API = "https://api.cloudflare.com/client/v4/accounts"


def request_json(method, url, token, payload=None):
    body = None if payload is None else payload.encode("utf-8")
    req = Request(url, data=body, method=method,
                  headers={"Authorization": f"Bearer {token}",
                           "Content-Type": "application/json"})
    with urlopen(req, timeout=30) as response:
        result = json.loads(response.read(4096))
    if result.get("success") is not True:
        raise RuntimeError("Cloudflare KV operation unsuccessful")
    return result


def publish(teams_path, players_path, *, account, namespace, token, activate=False):
    manifest = release_manifest(teams_path, players_path)
    release = manifest["keys"]["teams"]["sha256"][:16] + "-" + manifest["keys"]["players"]["sha256"][:16]
    base = f"{API}/{quote(account, safe='')}/storage/kv/namespaces/{quote(namespace, safe='')}/values/"
    for key, path in (("teams", teams_path), ("players", players_path)):
        raw = path.read_bytes()
        # Verify no changes occurred since manifest creation.
        import hashlib
        if hashlib.sha256(raw).hexdigest() != manifest["keys"][key]["sha256"]:
            raise ValueError("Dataset changed during release preparation")
        req = Request(base + quote(f"release:{release}:{key}", safe=""),
                      data=raw, method="PUT",
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type": "application/json"})
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read(4096))
        if result.get("success") is not True:
            raise RuntimeError("Versioned KV upload failed; active release unchanged")
    if activate:
        request_json("PUT", base + quote("active-release", safe=""), token,
                     json.dumps({"release": release}))
    return {"release": release, "activated": activate,
            "teamCount": manifest["teamCount"], "playerCount": manifest["playerCount"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("teams", type=Path)
    parser.add_argument("players", type=Path)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    manifest = release_manifest(args.teams, args.players)
    if not args.publish:
        print(json.dumps({"mode": "offline", "manifest": manifest}, indent=2))
        return
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    namespace = os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not all((account, namespace, token)):
        parser.error("Cloudflare account, namespace and API token secrets required")
    if args.activate:
        parser.error("Activation is disabled until Worker pointer-read tests pass")
    print(json.dumps(publish(args.teams, args.players, account=account,
                             namespace=namespace, token=token), indent=2))


if __name__ == "__main__":
    main()

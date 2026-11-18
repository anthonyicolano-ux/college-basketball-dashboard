"""Conservative CBBD season snapshot fetcher. No KV writes or public output.

Run only after permission review and explicit opt-in:
  CBBD_API_KEY=... python private-site/fetch_season_snapshot.py --allow-network --remaining-calls 800 --out PRIVATE_LOCAL_DIRECTORY
Default execution is offline and makes zero API calls. Never commit output files.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from api_budget import Budget, permit_refresh

BASE = "https://api.collegebasketballdata.com"
ENDPOINTS = ("stats/season/teams", "stats/season/players")


def plan(remaining):
    budget = Budget(remaining_calls=remaining, planned_calls=len(ENDPOINTS))
    if not permit_refresh(budget):
        raise ValueError("Insufficient shared quota after football and safety reserves")
    return tuple(f"{BASE}/{path}?season=2027" for path in ENDPOINTS)


def fetch_json(url, token):
    req = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=45) as response:
            raw = response.read(15_000_001)
    except HTTPError as exc:
        raise RuntimeError(f"Provider HTTP status {exc.code}; no data published") from None
    if len(raw) > 15_000_000:
        raise ValueError("Provider response exceeds configured limit")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Expected a list of season statistics")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--remaining-calls", type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not args.allow_network:
        print("DRY RUN: no network requests, no files written, no KV publication")
        return
    if args.remaining_calls is None or args.out is None:
        parser.error("Explicit remaining-call count and private output directory required")
    urls = plan(args.remaining_calls)
    token = os.environ.get("CBBD_API_KEY")
    if not token:
        parser.error("CBBD_API_KEY must be supplied as an environment secret")
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("Output directory must be empty to avoid overwriting snapshots")
    args.out.mkdir(parents=True, exist_ok=True)
    # Both calls must succeed before either raw snapshot is saved.
    datasets = [fetch_json(url, token) for url in urls]
    for name, data in zip(("raw-teams.json", "raw-players.json"), datasets):
        (args.out / name).write_text(json.dumps(data), encoding="utf-8")
    print("Saved two private raw snapshots; NOT normalized, validated, or published")


if __name__ == "__main__":
    main()

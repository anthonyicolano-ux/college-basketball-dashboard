"""Reconcile independently obtained NCAA men's basketball sport sponsorship evidence.

Input is a JSON array of objects with schoolName, ncaaDirectoryUrl, mensBasketballDivision.
The file must contain actual school-level evidence from the NCAA directory, not a
conference roster or a projected total. This tool does NOT fetch the NCAA website,
infer eligibility, or mark the release roster approved.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

def reconcile(matrix, evidence):
    schools = matrix.get("schoolEvidence", [])
    if len(schools) != 365 or len({x["schoolName"] for x in schools}) != 365:
        raise ValueError("Expected 365 unique candidate schools")
    if not isinstance(evidence, list):
        raise ValueError("Expected a list of NCAA school evidence records")
    names = {x["schoolName"] for x in schools}
    found = {}
    for item in evidence:
        name = item.get("schoolName")
        url = item.get("ncaaDirectoryUrl", "")
        division = item.get("mensBasketballDivision")
        parsed = urlparse(url)
        if name not in names or name in found:
            raise ValueError("Unknown or repeated school in NCAA evidence")
        if parsed.scheme != "https" or parsed.hostname != "web3.ncaa.org" or not parsed.path.startswith("/directory/orgDetail"):
            raise ValueError("NCAA organization detail URL required")
        if division not in ("I", "II", "III", "not_listed"):
            raise ValueError("Explicit sport-specific division required")
        found[name] = item
    rows = []
    for school in schools:
        name = school["schoolName"]
        item = found.get(name)
        status = ("confirmed" if item and item["mensBasketballDivision"] == "I"
                  else "discrepancy" if item else "pending")
        rows.append({"schoolName": name, "conference": school["conference"],
                     "status": status,
                     "ncaaDirectoryUrl": item["ncaaDirectoryUrl"] if item else None})
    counts = Counter(x["status"] for x in rows)
    groups = {}
    for row in rows:
        group = groups.setdefault(row["conference"], {"confirmed": 0, "pending": 0, "discrepancy": 0})
        group[row["status"]] += 1
    return {"season": 2027, "reviewed": False, "releaseApproved": False,
            "counts": dict(counts), "byConference": dict(sorted(groups.items())),
            "schools": rows}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--matrix", type=Path, required=True)
    p.add_argument("--ncaa-evidence", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        p.error("Refusing to overwrite prior reconciliation")
    result = reconcile(json.loads(args.matrix.read_text(encoding="utf-8")),
                       json.loads(args.ncaa_evidence.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("NCAA sponsorship reconciliation:", result["counts"])
    print("Release approval remains false; no provider API calls made.")

if __name__ == "__main__":
    main()

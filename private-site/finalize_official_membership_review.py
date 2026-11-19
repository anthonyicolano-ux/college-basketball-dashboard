"""Finalize evidence-backed 2026-27 men's basketball school review.

Requires an explicit decision and an NCAA source URL for EVERY candidate.
Does not fetch or infer eligibility. The resulting approved-name file is
compatible with resolve_reviewed_membership_from_kv.py.
"""
import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlparse

OFFICIAL_HOSTS={"web3.ncaa.org","www.ncaa.org","ncaa.org"}
REQUIRED={"schoolName","official2026_27MbbEvidence","eligible2026_27"}

def finalize(rows):
    if not 300<=len(rows)<=400:
        raise ValueError("Expected 300-400 reviewed candidate rows")
    seen=set()
    approved=[]
    for line,row in enumerate(rows,start=2):
        name=(row.get("schoolName") or "").strip()
        decision=(row.get("eligible2026_27") or "").strip().lower()
        source=(row.get("official2026_27MbbEvidence") or "").strip()
        if not name or name in seen:
            raise ValueError(f"Missing or duplicate school at row {line}")
        seen.add(name)
        if decision not in {"yes","no"}:
            raise ValueError(f"Missing explicit yes/no review at row {line}")
        parsed=urlparse(source)
        if parsed.scheme!="https" or (parsed.hostname or "").lower() not in OFFICIAL_HOSTS:
            raise ValueError(f"NCAA source URL required at row {line}")
        if decision=="yes":
            approved.append(name)
    if not 300<=len(approved)<=400:
        raise ValueError("Approved membership count outside expected range")
    return {"season":2027,"sport":"mens_basketball","reviewed":True,
            "schoolNames":approved}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("reviewed_csv",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite reviewed membership")
    with args.reviewed_csv.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not REQUIRED.issubset(reader.fieldnames or []):
            parser.error("Missing required review columns")
        result=finalize(list(reader))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(f"Finalized {len(result['schoolNames'])} reviewed school names; no provider calls")

if __name__=="__main__":
    main()

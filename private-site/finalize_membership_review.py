"""Convert a human-reviewed 2026-27 MBB team worksheet to an approved ID list.

Only explicit yes/no reviews are accepted. Every row must be reviewed;
ambiguous entries stop publication. This tool does not fetch data or guess.
"""
import argparse
import csv
import json
from pathlib import Path


def approved_membership(rows):
    if not rows:
        raise ValueError("Review worksheet is empty")
    ids, seen = [], set()
    for index, row in enumerate(rows, start=2):
        key = str(row.get("teamId", "")).strip()
        decision = str(row.get("divisionOneReview", "")).strip().lower()
        if not key or key in seen:
            raise ValueError(f"Missing or duplicate team ID at row {index}")
        seen.add(key)
        if decision not in ("yes", "no"):
            raise ValueError(f"Unreviewed or ambiguous membership at row {index}")
        if decision == "yes":
            ids.append(key)
    if not 300 <= len(ids) <= 400:
        raise ValueError("Reviewed Division I team count outside 300-400")
    return {"season": 2027, "reviewed": True, "teamIds": ids}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewed_csv", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite membership output")
    with args.reviewed_csv.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"teamId", "divisionOneReview"}
        if not required.issubset(set(reader.fieldnames or [])):
            parser.error("Worksheet must include teamId and divisionOneReview columns")
        result = approved_membership(list(reader))
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Approved membership file created for {len(result['teamIds'])} reviewed teams; no publication")


if __name__ == "__main__":
    main()

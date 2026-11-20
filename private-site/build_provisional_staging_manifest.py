"""Offline, non-approved candidate staging manifest. No provider calls or publication."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("schoolName", "conference", "conferenceAffiliation", "ncaaSportSponsorship",
          "fullDivisionOneMember", "championshipEligible", "ncaaSportSource")

def build(matrix):
    if matrix.get("season") != 2027 or matrix.get("reviewed") is not False:
        raise ValueError("Expected unapproved 2027 candidate evidence")
    schools = matrix.get("schoolEvidence")
    if not isinstance(schools, list) or len(schools) != 365:
        raise ValueError("Expected 365 provisional candidates")
    names = [s.get("schoolName") for s in schools]
    if any(not isinstance(n, str) or not n.strip() for n in names) or len(set(names)) != 365:
        raise ValueError("Duplicate or invalid candidate names")
    if any(s.get("conferenceAffiliation") != "checked" for s in schools):
        raise ValueError("Unreconciled conference affiliation")
    return [{field: school.get(field) or "" for field in FIELDS} for school in schools]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    matrix = json.loads((ROOT / "references/2026_27_mbb_school_evidence_matrix.json").read_text(encoding="utf-8"))
    rows = build(matrix)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "candidate-review.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = {"season": 2027, "candidate_count": len(rows),
              "ncaa_sport_evidence_pending": sum(r["ncaaSportSponsorship"] == "pending" for r in rows),
              "reviewed": False, "release_approved": False, "provider_calls": 0,
              "publication": "none"}
    (args.out / "staging-readiness.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()

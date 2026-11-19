"""Create a *draft* membership review worksheet from existing private team rows.

The output is NOT a reviewed Division I list and cannot be used for publication.
Review team membership against an authoritative 2026-27 MBB directory, then
build a separate reviewed file with season=2027, reviewed=true, teamIds=[...].
Never commit provider-derived draft lists or raw records.
"""
import argparse
import csv
import json
from pathlib import Path


def draft(rows):
    if not isinstance(rows, list):
        raise ValueError("Expected provider team list")
    seen = set()
    output = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid team row")
        team_id, team = row.get("teamId"), row.get("team")
        if isinstance(team_id, bool) or not isinstance(team_id, (int, str)) or not isinstance(team, str) or not team.strip():
            raise ValueError("Team ID or name missing")
        if str(team_id) in seen:
            raise ValueError("Duplicate team ID")
        seen.add(str(team_id))
        output.append({"teamId": str(team_id), "team": team,
                       "conference": str(row.get("conference") or ""),
                       "divisionOneReview": "", "reviewNotes": ""})
    return sorted(output, key=lambda r: r["team"].casefold())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_teams", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite an existing review worksheet")
    rows = draft(json.loads(args.raw_teams.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["teamId","team","conference","divisionOneReview","reviewNotes"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} unreviewed team entries; NOT an approved membership file")


if __name__ == "__main__":
    main()

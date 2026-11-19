"""Audit a reviewed Division I membership file against offline provider team rows.

Reports only aggregate counts and unmatched provider IDs/team labels for human
review. Never guesses Division I membership or calls any API.
"""
import argparse
import json
from pathlib import Path
from filter_division_one import load_approved_ids


def audit(rows, ids):
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Expected provider team objects")
    provider = {}
    for row in rows:
        if "teamId" not in row or "team" not in row:
            raise ValueError("Provider teamId/team missing")
        key = str(row["teamId"])
        if key in provider:
            raise ValueError("Duplicate provider teamId")
        provider[key] = row["team"]
    selected = {str(i) for i in ids}
    return {
        "providerTeamCount": len(provider),
        "approvedDivisionOneCount": len(selected),
        "matchedCount": len(selected & provider.keys()),
        "missingApprovedIds": sorted(selected - provider.keys()),
        "excludedProviderCount": len(provider.keys() - selected),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_teams", type=Path)
    parser.add_argument("--reviewed-membership", type=Path, required=True)
    args = parser.parse_args()
    report = audit(json.loads(args.raw_teams.read_text(encoding="utf-8")),
                   load_approved_ids(args.reviewed_membership))
    print(json.dumps(report, indent=2))
    if report["missingApprovedIds"]:
        raise SystemExit("Coverage incomplete; do not publish")


if __name__ == "__main__":
    main()

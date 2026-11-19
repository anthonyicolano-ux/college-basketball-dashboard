"""Offline reconcile the EXISTING 361-school candidate list with a provider worksheet.

This only proposes name matches; never grants Division I approval. Exact normalized
matches are suggestions, ambiguous names remain blank for human review.
No provider calls and no raw statistics are printed or published.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_bulk_candidate_matching import key, PROVIDER_NAME_ALIASES

CANDIDATES = ROOT / "references" / "di_mens_basketball_candidates_2026_27.json"


def reconcile(provider_rows, candidate_rows):
    index = {}
    for item in candidate_rows:
        name = item["name"]
        for alias in [name, *item.get("aliases", []), *PROVIDER_NAME_ALIASES.get(name, ())]:
            index.setdefault(key(alias), set()).add(name)
    output = []
    matched_names = set()
    for row in provider_rows:
        possible = index.get(key(row["team"]), set())
        match = next(iter(possible)) if len(possible) == 1 else ""
        if match:
            matched_names.add(match)
        output.append({**row, "candidateName": match,
                       "candidateMatchStatus": "name_match_only" if match else ("ambiguous" if possible else "unmatched"),
                       "divisionOneReview": "", "reviewNotes": ""})
    return output, {"providerRows": len(output), "matchedCandidateNames": len(matched_names),
                    "unmatchedCandidateNames": len({c["name"] for c in candidate_rows} - matched_names),
                    "unmatchedProviderRows": sum(x["candidateMatchStatus"] != "name_match_only" for x in output)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("provider_review_csv", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite existing review")
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))["candidates"]
    with args.provider_review_csv.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not {"teamId", "team"}.issubset(rows[0].keys() if rows else []):
        parser.error("Provider worksheet requires teamId and team")
    result, summary = reconcile(rows, candidates)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(result[0]))
        writer.writeheader()
        writer.writerows(result)
    print(json.dumps(summary, indent=2))
    print("ALL memberships remain unreviewed. Do not commit provider worksheets.")


if __name__ == "__main__":
    main()

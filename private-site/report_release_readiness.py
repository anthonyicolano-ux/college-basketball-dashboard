"""Summarize basketball release readiness from existing offline evidence.

No network calls, secrets, membership approval, or publishing.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def summarize(matrix, evidence):
    schools = matrix["schoolEvidence"]
    if len(schools) != 365 or len({s["schoolName"] for s in schools}) != 365:
        raise ValueError("Expected 365 unique school candidates")
    names = {s["schoolName"] for s in schools}
    confirmed = set()
    for item in evidence:
        name = item["schoolName"]
        if name not in names or name in confirmed:
            raise ValueError("Unknown or duplicate NCAA school evidence")
        if item.get("mensBasketballDivision") != "I":
            raise ValueError("Non-DI sport-specific evidence must be reviewed separately")
        if not item.get("ncaaDirectoryUrl", "").startswith("https://web3.ncaa.org/directory/orgDetail?id="):
            raise ValueError("Official NCAA directory URL required")
        confirmed.add(name)
    return {
        "candidate_schools": len(schools),
        "conference_affiliations_checked": sum(s["conferenceAffiliation"] == "checked" for s in schools),
        "ncaa_sport_sponsorship_confirmed": len(confirmed),
        "ncaa_sport_sponsorship_pending": len(schools) - len(confirmed),
        "release_approved": False,
        "api_calls_made": 0,
    }

def main():
    matrix = json.loads((ROOT / "references/2026_27_mbb_school_evidence_matrix.json").read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / "references/2026_27_mbb_ncaa_sport_evidence.json").read_text(encoding="utf-8"))
    summary = summarize(matrix, evidence)
    print("Basketball release readiness (offline):", json.dumps(summary, sort_keys=True))
    import os
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            out.write("## Basketball release readiness\n\n")
            out.write("| Check | Result |\n|---|---:|\n")
            for key, value in summary.items():
                out.write(f"| {key.replace('_', ' ').capitalize()} | {value} |\n")
            out.write("\nEvidence counts are not independent verification of the URLs' page content. Release remains blocked.\n")

if __name__ == "__main__":
    main()

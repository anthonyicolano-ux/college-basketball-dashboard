"""Build a source-traceable, explicitly UNREVIEWED 2026-27 MBB roster worksheet.

Uses repository candidate names only; no provider API calls, secrets or KV access.
This output is not eligibility evidence and cannot satisfy the release gate.
"""
import argparse
import csv
import json
from pathlib import Path

FIELDS=("schoolName","candidateConference","candidateSource","officialDirectory",
        "official2026_27MbbEvidence","eligible2026_27","reviewerNotes")

def make_rows(candidates,seed):
    if candidates.get("season")!=2027 or candidates.get("status")!="CANDIDATES_ONLY_NOT_ELIGIBILITY":
        raise ValueError("Unrecognized candidate reference")
    if seed.get("season")!=2027:
        raise ValueError("Wrong seed season")
    schools=list(candidates.get("candidates",[]))+list(seed.get("schools",[]))
    names=set()
    output=[]
    for school in schools:
        name=school.get("name")
        if not isinstance(name,str) or not name.strip() or name in names:
            raise ValueError("Missing or duplicate candidate school")
        names.add(name)
        output.append(dict(schoolName=name,candidateConference=school.get("conference",""),
                           candidateSource=school.get("source_url",""),
                           officialDirectory="https://web3.ncaa.org/directory/",
                           official2026_27MbbEvidence="",eligible2026_27="",reviewerNotes=""))
    if not 300<=len(output)<=400:
        raise ValueError("Unexpected school candidate count")
    return sorted(output,key=lambda row:row["schoolName"].casefold())

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidates",type=Path,default=Path("references/di_mens_basketball_candidates_2026_27.json"))
    parser.add_argument("--seed",type=Path,default=Path("references/di_mens_basketball_2026_27.json"))
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite worksheet")
    rows=make_rows(json.loads(args.candidates.read_text(encoding="utf-8")),
                   json.loads(args.seed.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {len(rows)} UNREVIEWED school entries; no approval or API calls")

if __name__=="__main__":
    main()

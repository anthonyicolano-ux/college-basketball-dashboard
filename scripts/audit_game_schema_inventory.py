"""Read-only, opt-in schema inventory for one CBBD /games response.
Prints aggregate field names and value types only; never game rows or values.
No KV writes, artifacts, or publication. Uses one API request only when invoked.
This is a diagnostic, not completed-game reconciliation.
"""
import json
import os
import sys
from collections import Counter
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SEASON = 2027
URL = "https://api.collegebasketballdata.com/games"


def inspect(rows):
    if not isinstance(rows, list):
        raise ValueError("Expected list")
    if len(rows) > 3000:
        raise ValueError("Unexpected result count")
    types = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected game object")
        for field, value in row.items():
            if not isinstance(field, str):
                raise ValueError("Invalid field")
            t = "null" if value is None else type(value).__name__
            types.setdefault(field, Counter())[t] += 1
    return {"season": SEASON, "records_returned": len(rows),
            "at_documented_result_cap": len(rows) == 3000,
            "field_types": {field: dict(sorted(counter.items()))
                            for field, counter in sorted(types.items())},
            "status": "SCHEMA_INVENTORY_ONLY_COMPLETION_NOT_VERIFIED"}


def main():
    if os.getenv("PUBLISH_EXPANDED_KV") or os.getenv("PUBLICATION_APPROVAL"):
        print("BLOCKED: schema inventory cannot publish.")
        return 2
    token = os.getenv("CBBD_API_KEY", "").strip()
    if not token:
        print("FAIL: missing CBBD_API_KEY")
        return 1
    try:
        query = urlencode({"season": SEASON})
        request = Request(URL + "?" + query, headers={"Authorization": "Bearer " + token,
                                                       "Accept": "application/json"})
        with urlopen(request, timeout=30) as response:
            rows = json.load(response)
        print("PRIVATE GAME SCHEMA INVENTORY: " + json.dumps(inspect(rows), sort_keys=True))
        print("READ ONLY: one provider request, no raw game values, KV writes or publication.")
        return 0
    except Exception as error:
        print("FAIL: game schema inventory; error_type=" + type(error).__name__ +
              "; no raw provider rows or credentials logged.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

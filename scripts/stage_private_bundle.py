"""Stage validated basketball JSON in a separate local private-deployment folder.

This command never uploads or publishes files and refuses to write inside the
repository. A deployment operator must separately verify licensing and access.
Usage: python scripts/stage_private_bundle.py SOURCE_DIR DEST_DIR
"""
import json
import shutil
import sys
from pathlib import Path
from check_private_bundle import check_bundle, FILES

ROOT = Path(__file__).resolve().parents[1]


def stage(source, destination):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError("Destination must be outside the public repository")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("Source and destination must be separate folders")
    if destination.exists():
        raise ValueError("Destination must not exist (use a fresh private directory)")
    counts = check_bundle(source)
    destination.mkdir(parents=True, exist_ok=True)
    try:
        for filename in FILES:
            shutil.copyfile(source / filename, destination / filename)
        # No secrets or personal data are written to the manifest.
        (destination / "deployment-manifest.json").write_text(
            json.dumps({"schemaVersion": 1, "season": 2027,
                        "files": list(FILES), "recordCounts": counts,
                        "privateDeploymentOnly": True}, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        for filename in (*FILES, "deployment-manifest.json"):
            (destination / filename).unlink(missing_ok=True)
        raise
    return counts


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/stage_private_bundle.py SOURCE_DIR DEST_DIR")
    try:
        counts = stage(sys.argv[1], sys.argv[2])
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Private staging rejected: {exc}")
    print("Validated bundle staged locally outside repository; no deployment performed.")
    print("Records: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("Confirm provider rights and authenticated Cloudflare delivery before publishing.")

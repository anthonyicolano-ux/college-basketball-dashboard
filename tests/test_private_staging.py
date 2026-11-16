"""Synthetic tests for local-only staging; no provider records or network."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from stage_private_bundle import stage, ROOT


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source"
        self.source.mkdir()
        self.destination = Path(self.temp.name) / "private"
        common = {"schemaVersion": 1, "season": 2027, "demo": False,
                  "approvedForPrivateDisplay": True, "generatedAt": "2026-11-16T00:00:00Z",
                  "scope": "Synthetic test fixture", "source": "synthetic fixture"}
        self.write("teams.json", dict(common, rows=[{"team": "Example A", "games": 3, "wins": 2, "losses": 1}]))
        self.write("players.json", dict(common, rows=[{"name": "Example Player", "team": "Example A", "games": 3}]))

    def write(self, name, obj):
        (self.source / name).write_text(json.dumps(obj), encoding="utf-8")

    def test_stages_only_expected_files(self):
        counts = stage(self.source, self.destination)
        self.assertEqual(counts["teams.json"], 1)
        self.assertEqual({p.name for p in self.destination.iterdir()},
                         {"teams.json", "players.json", "deployment-manifest.json"})
        self.assertTrue(json.loads((self.destination / "deployment-manifest.json").read_text())["privateDeploymentOnly"])

    def test_rejects_invalid_records_before_copy(self):
        self.write("teams.json", {"demo": True})
        with self.assertRaises(ValueError):
            stage(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_rejects_nonempty_destination(self):
        self.destination.mkdir()
        (self.destination / "existing.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must not exist"):
            stage(self.source, self.destination)

    def test_rejects_public_repository_destination(self):
        with self.assertRaisesRegex(ValueError, "outside the public repository"):
            stage(self.source, ROOT / "data" / "private")


if __name__ == "__main__":
    unittest.main()

"""Unit tests for local private-bundle validation; synthetic fixtures only."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_private_bundle import check_bundle


class PrivateBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.teams = {"schemaVersion": 1, "season": 2027, "demo": False,
                      "approvedForPrivateDisplay": True, "generatedAt": "2026-11-16T00:00:00Z",
                      "scope": "Synthetic fixture only", "source": "synthetic test fixture",
                      "rows": [{"team": "Example A", "games": 3, "wins": 2, "losses": 1}]}
        self.players = dict(self.teams, rows=[{"name": "Example Player", "team": "Example A", "games": 3}])
        self.save()

    def save(self):
        (self.folder / "teams.json").write_text(json.dumps(self.teams), encoding="utf-8")
        (self.folder / "players.json").write_text(json.dumps(self.players), encoding="utf-8")

    def test_valid_fixture(self):
        self.assertEqual(check_bundle(self.folder), {"teams.json": 1, "players.json": 1})

    def test_demo_rejected(self):
        self.players["demo"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "not a real dataset"):
            check_bundle(self.folder)

    def test_missing_approval_rejected(self):
        self.teams["approvedForPrivateDisplay"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "approval missing"):
            check_bundle(self.folder)

    def test_unresolved_team_record_rejected(self):
        self.teams["rows"][0]["games"] = 4
        self.save()
        with self.assertRaisesRegex(ValueError, "unresolved team record"):
            check_bundle(self.folder)

    def test_missing_provenance_rejected(self):
        self.players["source"] = ""
        self.save()
        with self.assertRaisesRegex(ValueError, "source missing"):
            check_bundle(self.folder)

    def test_wrong_season_rejected(self):
        self.teams["season"] = 2026
        self.save()
        with self.assertRaisesRegex(ValueError, "invalid schema or season"):
            check_bundle(self.folder)

    def test_missing_player_team_rejected(self):
        self.players["rows"][0].pop("team")
        self.save()
        with self.assertRaisesRegex(ValueError, "missing player team"):
            check_bundle(self.folder)


if __name__ == "__main__":
    unittest.main()

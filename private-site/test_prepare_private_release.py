import json
import tempfile
import unittest
from pathlib import Path
from prepare_private_release import release_manifest


class ReleaseManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        meta = dict(schemaVersion=1, season=2027, demo=False,
                    approvedForPrivateDisplay=True, source="Synthetic Test",
                    scope="Test only", generatedAt="2026-11-18T00:00:00+00:00")
        teams = [dict(team=f"Team {i}", conference="X", wins=1, losses=0,
                      games=1, ppg=70, oppPpg=60, offRating=100,
                      defRating=90, netRating=10, scoringMargin=10)
                 for i in range(365)]
        players = [dict(id=i, name=f"Player {i}", team=f"Team {i % 365}",
                        games=1, points=12, rebounds=3, assists=2, minutes=20)
                   for i in range(365)]
        self.teams = self.root / "teams.json"
        self.players = self.root / "players.json"
        self.teams.write_text(json.dumps({**meta, "rows": teams}))
        self.players.write_text(json.dumps({**meta, "rows": players}))

    def test_valid_release_plan(self):
        plan = release_manifest(self.teams, self.players)
        self.assertEqual(plan["teamCount"], 365)
        self.assertEqual(plan["playerCount"], 365)
        self.assertEqual(len(plan["keys"]["teams"]["sha256"]), 64)

    def test_mismatched_timestamp_rejected(self):
        data = json.loads(self.players.read_text())
        data["generatedAt"] = "2026-11-19T00:00:00+00:00"
        self.players.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "timestamp"):
            release_manifest(self.teams, self.players)

    def test_partial_coverage_rejected(self):
        data = json.loads(self.teams.read_text())
        data["rows"] = data["rows"][:24]
        self.teams.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "partial team"):
            release_manifest(self.teams, self.players)


if __name__ == "__main__":
    unittest.main()

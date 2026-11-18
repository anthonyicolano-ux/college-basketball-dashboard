"""Regression checks for private dataset validation; no provider data or network."""
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from validate_full_coverage import validate_teams, validate_players, load
import json
import tempfile
from pathlib import Path


def bundle(rows):
    return {
        "schemaVersion": 1, "season": 2027, "demo": False,
        "approvedForPrivateDisplay": True, "source": "synthetic test fixture",
        "scope": "local validation only",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
    }


def team(name):
    return {
        "team": name, "conference": "Test",
        "wins": 2, "losses": 1, "games": 3,
        "ppg": 70, "oppPpg": 65, "offRating": 105,
        "defRating": 98, "netRating": 7, "scoringMargin": 5,
    }


def player(name, team_name):
    return {"name": name, "team": team_name, "games": 3,
            "points": 10, "rebounds": 4, "assists": 2, "minutes": 20}


class CoverageValidationTests(unittest.TestCase):
    def setUp(self):
        self.teams = bundle([team("Test A"), team("Test B")])
        self.players = bundle([player("Test Player", "Test A")])

    def test_valid_pair(self):
        names = validate_teams(self.teams)
        validate_players(self.players, names)
        self.assertEqual(names, {"Test A", "Test B"})

    def test_duplicate_team_rejected(self):
        self.teams["rows"][1]["team"] = "Test A"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_teams(self.teams)

    def test_unreconciled_record_rejected(self):
        self.teams["rows"][0]["games"] = 4
        with self.assertRaisesRegex(ValueError, "Unreconciled"):
            validate_teams(self.teams)

    def test_nonfinite_metric_rejected(self):
        self.teams["rows"][0]["ppg"] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            validate_teams(self.teams)

    def test_malformed_player_team_rejected(self):
        self.players["rows"][0]["team"] = ["not", "a", "team"]
        with self.assertRaisesRegex(ValueError, "outside covered"):
            validate_players(self.players, validate_teams(self.teams))

    def test_unknown_player_team_rejected(self):
        self.players["rows"][0]["team"] = "Unknown"
        with self.assertRaisesRegex(ValueError, "outside covered"):
            validate_players(self.players, validate_teams(self.teams))

    def test_duplicate_player_id_rejected(self):
        first = self.players["rows"][0]
        first["id"] = "p1"
        second = deepcopy(first)
        self.players["rows"].append(second)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_players(self.players, validate_teams(self.teams))

    def test_missing_approval_rejected(self):
        self.teams["approvedForPrivateDisplay"] = False
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "teams.json"
            path.write_text(json.dumps(self.teams), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approval"):
                load(path)

    def test_invalid_timestamp_rejected(self):
        self.teams["generatedAt"] = "not-a-date"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "teams.json"
            path.write_text(json.dumps(self.teams), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "timestamp"):
                load(path)

    def test_full_coverage_synthetic_scale(self):
        self.teams["rows"] = [team(f"Test {i}") for i in range(365)]
        self.players["rows"] = [
            player(f"Player {i}", f"Test {i % 365}") for i in range(5500)
        ]
        covered = validate_teams(self.teams)
        validate_players(self.players, covered)
        self.assertEqual(len(covered), 365)

    def test_full_coverage_missing_team_rejected(self):
        self.teams["rows"] = [team(f"Test {i}") for i in range(365)]
        self.players["rows"] = [player("Unmatched Player", "Not Covered")]
        with self.assertRaisesRegex(ValueError, "outside covered"):
            validate_players(self.players, validate_teams(self.teams))

    def test_oversized_team_dataset_rejected(self):
        self.teams["rows"] = [team(f"Test {i}") for i in range(401)]
        with self.assertRaisesRegex(ValueError, "count"):
            validate_teams(self.teams)


if __name__ == "__main__":
    unittest.main()

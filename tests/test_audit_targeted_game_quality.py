"""Offline tests for targeted aggregate game quality."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_targeted_game_quality import inspect_targets


class TargetedGameQualityTests(unittest.TestCase):
    def test_aggregate_without_game_details(self):
        rows = [
            {"id": 100, "homeTeam": "Bethune-Cookman", "awayTeam": "Other",
             "status": "final", "homePoints": 70, "awayPoints": 60,
             "homeWinner": True, "awayWinner": False},
            {"id": 101, "homeTeam": "Other", "awayTeam": "North Carolina A&T",
             "status": "final", "homePoints": 65, "awayPoints": 60,
             "homeWinner": None, "awayWinner": None},
            {"id": 102, "homeTeam": "Bethune-Cookman", "awayTeam": "Other",
             "status": "scheduled", "homePoints": None, "awayPoints": None},
        ]
        result = inspect_targets(rows)
        self.assertEqual(result["targets"]["Bethune-Cookman"]["validated_final"], 1)
        self.assertEqual(result["targets"]["Bethune-Cookman"]["nonfinal_or_unknown"], 1)
        self.assertEqual(result["targets"]["North Carolina A&T"]["unresolved_final"], 1)
        self.assertNotIn("100", str(result))
        self.assertEqual(result["coverage"], "CAPPED_RESPONSE_NOT_SEASON_TOTALS")

    def test_categorizes_missing_winner_flags(self):
        row = {"homeTeam": "Bethune-Cookman", "awayTeam": "Other", "status": "final",
               "homePoints": 70, "awayPoints": 60, "homeWinner": None, "awayWinner": None}
        result = inspect_targets([row])["targets"]["Bethune-Cookman"]
        self.assertEqual(result["missing_winner_flags_with_valid_score"], 1)
        self.assertEqual(result["unresolved_final"], 1)

    def test_rejects_invalid_rows(self):
        with self.assertRaises(ValueError):
            inspect_targets([None])

    def test_rejects_duplicate_target_labels(self):
        with self.assertRaises(ValueError):
            inspect_targets([], ("A", "A"))


if __name__ == "__main__":
    unittest.main()

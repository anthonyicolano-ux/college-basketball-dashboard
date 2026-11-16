"""Offline-only checks for completed game reconciliation diagnostics."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_completed_games_offline import review


class CompletedGamesOfflineTests(unittest.TestCase):
    def test_completed_wins_losses_and_unresolved(self):
        games = [
            {"id": 1, "homeTeam": "Alabama A&M", "awayTeam": "Opponent",
             "completed": True, "homePoints": 75, "awayPoints": 70},
            {"id": 2, "homeTeam": "Opponent", "awayTeam": "Alabama A&M",
             "completed": True, "homePoints": 80, "awayPoints": 60},
            {"id": 3, "homeTeam": "Alabama A&M", "awayTeam": "Opponent",
             "completed": False},
            {"id": 1, "homeTeam": "Alabama A&M", "awayTeam": "Opponent",
             "completed": True, "homePoints": 75, "awayPoints": 70},
        ]
        result = review(games, {"Alabama A&M": ["Alabama A&M"]})
        self.assertEqual(result["unique_input_games"], 3)
        self.assertEqual(result["teams"]["Alabama A&M"],
                         {"observed_games": 3, "scored_completed_games": 2,
                          "unresolved_status_or_score": 1, "wins": 1, "losses": 1})
        self.assertIn("PARTIAL_COVERAGE", result["status"])

    def test_ambiguous_alias_is_rejected(self):
        with self.assertRaises(ValueError):
            review([], {"Alabama A&M": ["X"], "Princeton": ["X"]})

    def test_missing_game_id_is_rejected(self):
        with self.assertRaises(ValueError):
            review([{"completed": True}], {})

    def test_tied_score_not_counted_as_win_or_loss(self):
        result = review([{"id": 9, "homeTeam": "Princeton", "awayTeam": "X",
                          "completed": True, "homePoints": 70, "awayPoints": 70}],
                        {"Princeton": ["Princeton"]})
        self.assertEqual(result["teams"]["Princeton"]["unresolved_status_or_score"], 1)


if __name__ == "__main__":
    unittest.main()

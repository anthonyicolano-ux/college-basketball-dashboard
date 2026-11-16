"""Offline tests for strict CBBD final-game classification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from review_completed_games_offline import review


def game(i, home="South Dakota", away="Opponent", status="final",
         hp=70, ap=60, hw=True, aw=False):
    return {"id": i, "homeTeam": home, "awayTeam": away, "status": status,
            "homePoints": hp, "awayPoints": ap, "homeWinner": hw, "awayWinner": aw}


class CompletedGamesOfflineTests(unittest.TestCase):
    def test_valid_final_wins_losses_and_dedup(self):
        rows = [game(1), game(2, home="Opponent", away="South Dakota",
                              hp=75, ap=65), game(1)]
        r = review(rows, {"South Dakota": ["South Dakota"]})
        self.assertEqual(r["unique_input_games"], 2)
        self.assertEqual(r["teams"]["South Dakota"]["wins"], 1)
        self.assertEqual(r["teams"]["South Dakota"]["losses"], 1)
        self.assertIn("PARTIAL", r["status"])

    def test_conflicting_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            review([game(1), game(1, hp=71)], {"South Dakota": ["South Dakota"]})

    def test_unresolved_status_and_missing_winner(self):
        rows = [game(1, status="scheduled", hp=None, ap=None, hw=None, aw=None),
                game(2, status="postponed", hp=None, ap=None, hw=None, aw=None),
                game(3, hw=None, aw=None), game(4, hp=70, ap=70),
                game(5, hw=False, aw=True), game(6, status="unknown")]
        r = review(rows, {"South Dakota": ["South Dakota"]})
        self.assertEqual(r["teams"]["South Dakota"]["unresolved_status_or_score"], 6)
        self.assertNotIn("wins", r["teams"]["South Dakota"])

    def test_missing_required_field_rejected(self):
        row = game(1)
        del row["awayWinner"]
        with self.assertRaises(ValueError):
            review([row], {"South Dakota": ["South Dakota"]})

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            review([game(1, status=None)], {"South Dakota": ["South Dakota"]})

    def test_ambiguous_alias_rejected(self):
        with self.assertRaises(ValueError):
            review([], {"A": ["Same"], "B": ["Same"]})

    def test_empty_targets_rejected(self):
        with self.assertRaises(ValueError):
            review([], {})

    def test_missing_id_rejected(self):
        row = game(1)
        del row["id"]
        with self.assertRaises(ValueError):
            review([row], {"South Dakota": ["South Dakota"]})

    def test_no_season_total_claim(self):
        r = review([game(1)], {"South Dakota": ["South Dakota"]})
        self.assertEqual(r["coverage"], "PARTIAL_OR_UNKNOWN_NEVER_SEASON_TOTALS")


if __name__ == "__main__":
    unittest.main()

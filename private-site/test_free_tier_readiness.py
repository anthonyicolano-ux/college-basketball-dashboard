import unittest
from free_tier_readiness import inspect_snapshot


class FreeTierReadinessTests(unittest.TestCase):
    def test_basic_stats_do_not_require_paid_ratings(self):
        teams = [dict(team="Synthetic", games=2, wins=1, losses=1, ppg=70, oppPpg=68)]
        players = [dict(name="Example", team="Synthetic", games=2,
                        points=12, rebounds=4, assists=3, minutes=25)]
        result = inspect_snapshot(teams, players)
        self.assertTrue(result["teams"]["basicReady"])
        self.assertTrue(result["players"]["basicReady"])

    def test_missing_basic_stat_reported(self):
        result = inspect_snapshot([dict(team="A")], [dict(name="B")])
        self.assertFalse(result["teams"]["basicReady"])
        self.assertEqual(result["teams"]["missing"]["games"], 1)

    def test_reject_non_list(self):
        with self.assertRaises(ValueError):
            inspect_snapshot({}, [])


if __name__ == "__main__":
    unittest.main()

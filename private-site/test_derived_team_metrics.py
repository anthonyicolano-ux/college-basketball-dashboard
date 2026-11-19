import unittest
from derived_team_metrics import derive_team_metrics


class DerivedTeamMetricsTests(unittest.TestCase):
    def test_valid_team(self):
        row = dict(games=4, wins=3, losses=1, ppg=81.5, oppPpg=72.0,
                   offRating=112.2, defRating=101.4)
        self.assertEqual(derive_team_metrics(row),
                         dict(winPct=0.75, calculatedScoringMargin=9.5,
                              calculatedNetRating=10.8))

    def test_zero_games_has_no_win_percentage(self):
        row = dict(games=0, wins=0, losses=0, ppg=0, oppPpg=0,
                   offRating=0, defRating=0)
        self.assertIsNone(derive_team_metrics(row)["winPct"])

    def test_missing_input_fails_closed(self):
        with self.assertRaises(ValueError):
            derive_team_metrics(dict(games=2, wins=1, losses=1))

    def test_inconsistent_record_fails(self):
        with self.assertRaises(ValueError):
            derive_team_metrics(dict(games=3, wins=2, losses=2, ppg=70,
                                     oppPpg=60, offRating=100, defRating=90))

    def test_boolean_not_number(self):
        with self.assertRaises(ValueError):
            derive_team_metrics(dict(games=True, wins=1, losses=0, ppg=70,
                                     oppPpg=60, offRating=100, defRating=90))


if __name__ == "__main__":
    unittest.main()

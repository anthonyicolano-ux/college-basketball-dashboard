import unittest
from normalize_season_snapshot import build


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.teams = [
            dict(team="A", conference="X", games=1, wins=1, losses=0,
                 ppg=80, oppPpg=70, offRating=110, defRating=100,
                 netRating=10, scoringMargin=10),
            dict(team="B", conference="X", games=1, wins=0, losses=1,
                 ppg=70, oppPpg=80, offRating=100, defRating=110,
                 netRating=-10, scoringMargin=-10),
        ]
        self.players = [dict(name="Example", team="A", games=1,
                             points=12, rebounds=4, assists=2, minutes=25)]

    def test_valid_exact_shape(self):
        with self.assertRaisesRegex(ValueError, "at least 300"):
            build(self.teams, self.players, display_permission_confirmed=True,
                  expected_team_count=2)

    def test_requires_permission(self):
        with self.assertRaises(ValueError):
            build(self.teams, self.players)

    def test_missing_fields_fail_instead_of_guessing(self):
        del self.teams[0]["offRating"]
        with self.assertRaisesRegex(ValueError, "mapping required"):
            build(self.teams, self.players, display_permission_confirmed=True,
                  expected_team_count=365)

    def test_verified_full_coverage(self):
        teams = [dict(self.teams[0], team=f"Team {i}") for i in range(365)]
        players = [dict(self.players[0], team="Team 0")]
        output, people = build(teams, players, display_permission_confirmed=True,
                               expected_team_count=365)
        self.assertEqual(len(output["rows"]), 365)
        self.assertEqual(len(people["rows"]), 1)

    def test_count_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "Incomplete team coverage"):
            build(self.teams, self.players, display_permission_confirmed=True,
                  expected_team_count=365)

    def test_unknown_team_rejected(self):
        self.players[0]["team"] = "Unknown"
        with self.assertRaises(ValueError):
            build(self.teams, self.players, display_permission_confirmed=True)


if __name__ == "__main__":
    unittest.main()

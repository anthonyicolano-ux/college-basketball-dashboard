import unittest
from verified_2027_provider_mapping import map_team, map_player

class TestProvider2027(unittest.TestCase):
    def test_team_totals_to_per_game(self):
        row = {"team": "Example", "teamId": 5, "conference": "C", "games": 4,
               "wins": 3, "losses": 1,
               "teamStats": {"points": {"total": 320}, "rating": 110},
               "opponentStats": {"points": {"total": 280}, "rating": 98}}
        mapped = map_team(row)
        self.assertEqual(mapped["teamId"], 5)
        self.assertEqual(mapped["ppg"], 80)
        self.assertEqual(mapped["oppPpg"], 70)
        self.assertEqual(mapped["scoringMargin"], 10)
        self.assertEqual(mapped["netRating"], 12)

    def test_player_id_and_rebounds(self):
        row = {"name": "Example", "team": "Example", "teamId": 5,
               "games": 4, "points": 50, "rebounds": {"total": 20},
               "assists": 7, "minutes": 100, "athleteId": 123}
        self.assertEqual(map_player(row)["rebounds"], 20)
        self.assertEqual(map_player(row)["id"], 123)

    def test_rejects_zero_games(self):
        row = {"team": "Example", "teamId": 5, "conference": "C", "games": 0,
               "wins": 0, "losses": 0,
               "teamStats": {"points": {"total": 0}, "rating": 0},
               "opponentStats": {"points": {"total": 0}, "rating": 0}}
        with self.assertRaisesRegex(ValueError, "Zero-game"):
            map_team(row)

if __name__ == "__main__":
    unittest.main()

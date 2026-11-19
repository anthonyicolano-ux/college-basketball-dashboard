import unittest
from prepare_real_2027 import prepare

def team(i):
    return {"team": f"Team {i}", "teamId": i, "conference": "Test",
            "games": 3, "wins": 2, "losses": 1,
            "teamStats": {"points": {"total": 210}, "rating": 105},
            "opponentStats": {"points": {"total": 198}, "rating": 99}}

def player(i):
    return {"name": f"Player {i}", "team": f"Team {i}", "teamId": i,
            "athleteId": 1000 + i, "games": 3, "points": 30,
            "rebounds": {"total": 15}, "assists": 6, "minutes": 60}

class TestPrepareReal2027(unittest.TestCase):
    def setUp(self):
        self.ids = list(range(1, 301))
        self.teams = [team(i) for i in self.ids] + [team(301)]
        self.players = [player(i) for i in self.ids] + [player(301)]

    def test_full_offline_pipeline(self):
        teams, players = prepare(self.teams, self.players, self.ids)
        self.assertEqual(len(teams["rows"]), 300)
        self.assertEqual(len(players["rows"]), 300)
        self.assertFalse(teams["demo"])
        self.assertEqual(teams["rows"][0]["ppg"], 70)
        self.assertEqual(teams["rows"][0]["netRating"], 6)
        self.assertEqual(players["rows"][0]["rebounds"], 15)

    def test_rejects_player_team_mismatch(self):
        self.players[0]["team"] = "Incorrect Team"
        with self.assertRaisesRegex(ValueError, "team name disagrees"):
            prepare(self.teams, self.players, self.ids)

    def test_rejects_missing_team(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            prepare(self.teams[1:], self.players, self.ids)

if __name__ == "__main__":
    unittest.main()

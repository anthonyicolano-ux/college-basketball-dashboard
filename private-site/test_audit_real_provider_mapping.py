import unittest
from audit_real_provider_mapping import inspect
from verified_2027_provider_mapping import TEAM_PATHS, PLAYER_PATHS


def team():
    return {"team": "Test", "teamId": 1, "conference": "Example", "games": 3,
            "wins": 2, "losses": 1,
            "teamStats": {"points": {"total": 240}, "rating": 110},
            "opponentStats": {"points": {"total": 210}, "rating": 100}}


def player():
    return {"name": "Test Player", "team": "Test", "teamId": 1,
            "games": 3, "points": 36, "rebounds": {"total": 12},
            "assists": 6, "minutes": 90, "athleteId": 5}


class TestRealProviderAudit(unittest.TestCase):
    def test_complete_team(self):
        report = inspect([team()], TEAM_PATHS)
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["missingByField"], {})
        self.assertEqual(report["wrongTypeByField"], {})

    def test_missing_nested_field(self):
        row = team()
        del row["opponentStats"]["rating"]
        report = inspect([row], TEAM_PATHS)
        self.assertEqual(report["missingByField"], {"defRating": 1})

    def test_zero_games_reported(self):
        row = team()
        row["games"] = 0
        self.assertEqual(inspect([row], TEAM_PATHS)["zeroGameRecords"], 1)

    def test_complete_player(self):
        report = inspect([player()], PLAYER_PATHS)
        self.assertEqual(report["missingByField"], {})

    def test_missing_player_rebounds(self):
        row = player()
        del row["rebounds"]["total"]
        self.assertEqual(inspect([row], PLAYER_PATHS)["missingByField"], {"rebounds": 1})

    def test_non_object_rejected(self):
        with self.assertRaises(ValueError):
            inspect(["invalid"], TEAM_PATHS)


if __name__ == "__main__":
    unittest.main()

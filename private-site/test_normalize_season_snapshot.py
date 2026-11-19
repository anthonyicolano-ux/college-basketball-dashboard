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

    def test_nested_mapping_full_coverage(self):
        teams = [dict(self.teams[0], team=f"Team {i}") for i in range(365)]
        raw_teams = [{"identity": {"team": row["team"]}, "metrics": row} for row in teams]
        raw_players = [{"identity": {"name": "Example", "team": "Team 0"},
                        "metrics": self.players[0]}]
        team_map = {key: f"metrics.{key}" for key in teams[0]}
        team_map["team"] = "identity.team"
        player_map = {key: f"metrics.{key}" for key in self.players[0]}
        player_map.update(name="identity.name", team="identity.team")
        output, people = build(raw_teams, raw_players,
                               display_permission_confirmed=True,
                               expected_team_count=365,
                               team_field_paths=team_map,
                               player_field_paths=player_map)
        self.assertEqual(len(output["rows"]), 365)
        self.assertEqual(people["rows"][0]["team"], "Team 0")

    def test_derived_fields_added(self):
        teams = [dict(self.teams[0], team=f"Team {i}") for i in range(365)]
        players = [dict(self.players[0], team="Team 0")]
        result, _ = build(teams, players, display_permission_confirmed=True,
                          expected_team_count=365)
        self.assertEqual(result["rows"][0]["winPct"], 1.0)
        self.assertEqual(result["rows"][0]["calculatedScoringMargin"], 10)
        self.assertEqual(result["rows"][0]["calculatedNetRating"], 10)

    def test_inconsistent_scoring_margin_rejected(self):
        teams = [dict(self.teams[0], team=f"Team {i}") for i in range(365)]
        teams[0]["scoringMargin"] = 25
        players = [dict(self.players[0], team="Team 0")]
        with self.assertRaisesRegex(ValueError, "Scoring margin disagrees"):
            build(teams, players, display_permission_confirmed=True,
                  expected_team_count=365)

    def test_inconsistent_net_rating_rejected(self):
        teams = [dict(self.teams[0], team=f"Team {i}") for i in range(365)]
        teams[0]["netRating"] = 99
        players = [dict(self.players[0], team="Team 0")]
        with self.assertRaisesRegex(ValueError, "Net rating disagrees"):
            build(teams, players, display_permission_confirmed=True,
                  expected_team_count=365)

    def test_partial_mapping_rejected(self):
        with self.assertRaisesRegex(ValueError, "Both provider"):
            build(self.teams, self.players, display_permission_confirmed=True,
                  expected_team_count=365, team_field_paths={"team": "team"})

    def test_unknown_team_rejected(self):
        self.players[0]["team"] = "Unknown"
        with self.assertRaises(ValueError):
            build(self.teams, self.players, display_permission_confirmed=True)


if __name__ == "__main__":
    unittest.main()

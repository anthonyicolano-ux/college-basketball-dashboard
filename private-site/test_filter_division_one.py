import unittest
from filter_division_one import filter_division_one, load_approved_ids


class TestDivisionOne(unittest.TestCase):
    def setUp(self):
        self.ids = list(range(1, 301))
        self.teams = [{"teamId": i, "team": str(i)} for i in range(1, 302)]
        self.players = [{"teamId": i, "name": "Player"} for i in range(1, 302)]

    def test_filters_non_division_one(self):
        teams, players = filter_division_one(self.teams, self.players, self.ids)
        self.assertEqual(len(teams), 300)
        self.assertEqual(len(players), 300)
        self.assertNotIn(301, [t["teamId"] for t in teams])

    def test_rejects_missing_approved_team(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            filter_division_one(self.teams[:-2], self.players, self.ids)

    def test_rejects_duplicate_provider_team(self):
        with self.assertRaisesRegex(ValueError, "Duplicate provider"):
            filter_division_one(self.teams + [self.teams[0]], self.players, self.ids)

    def test_rejects_unreviewed_shortcut(self):
        with self.assertRaisesRegex(ValueError, "300-400"):
            filter_division_one(self.teams, self.players, [1, 2])


if __name__ == "__main__":
    unittest.main()

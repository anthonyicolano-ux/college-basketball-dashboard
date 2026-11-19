import unittest
from suggest_provider_mapping import suggest, TEAM_CANDIDATES


class MappingSuggestionsTests(unittest.TestCase):
    def test_suggests_only_complete_paths(self):
        inventory={"paths":[{"path":"team","missing":0},
                            {"path":"stats.pointsPerGame","missing":2}]}
        result=suggest(inventory,TEAM_CANDIDATES)
        self.assertEqual(result["team"]["candidatePaths"],["team"])
        self.assertEqual(result["ppg"]["candidatePaths"],[])
        self.assertTrue(result["team"]["requiresReview"])

    def test_rejects_bad_inventory(self):
        with self.assertRaises(ValueError):
            suggest({},TEAM_CANDIDATES)


if __name__=="__main__":
    unittest.main()

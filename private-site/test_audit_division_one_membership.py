import unittest
from audit_division_one_membership import audit

class TestAuditDivisionOneMembership(unittest.TestCase):
    def test_counts_and_missing_ids(self):
        rows = [{"teamId": i, "team": f"Team {i}"} for i in range(1, 302)]
        report = audit(rows, list(range(1, 301)))
        self.assertEqual(report["providerTeamCount"], 301)
        self.assertEqual(report["matchedCount"], 300)
        self.assertEqual(report["excludedProviderCount"], 1)
        self.assertEqual(report["missingApprovedIds"], [])

    def test_missing_team_reported(self):
        report = audit([{"teamId": 1, "team": "A"}], [1, 2])
        self.assertEqual(report["missingApprovedIds"], ["2"])

    def test_duplicate_provider_id_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            audit([{"teamId": 1, "team": "A"}, {"teamId": 1, "team": "B"}], [1])

if __name__ == "__main__":
    unittest.main()

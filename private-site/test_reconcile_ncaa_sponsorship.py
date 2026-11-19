import unittest
from reconcile_ncaa_sponsorship import reconcile

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.matrix = {"schoolEvidence": [{"schoolName": f"School {i}", "conference": "Test"} for i in range(365)]}
    def test_no_evidence_is_pending(self):
        result = reconcile(self.matrix, [])
        self.assertEqual(result["counts"]["pending"], 365)
        self.assertFalse(result["releaseApproved"])
    def test_valid_evidence(self):
        result = reconcile(self.matrix, [{"schoolName":"School 0","ncaaDirectoryUrl":"https://web3.ncaa.org/directory/orgDetail?id=1","mensBasketballDivision":"I"}])
        self.assertEqual(result["counts"]["confirmed"], 1)
    def test_rejects_non_ncaa(self):
        with self.assertRaises(ValueError):
            reconcile(self.matrix, [{"schoolName":"School 0","ncaaDirectoryUrl":"https://example.com/directory/orgDetail?id=1","mensBasketballDivision":"I"}])
    def test_flags_non_division_one(self):
        result = reconcile(self.matrix, [{"schoolName":"School 0","ncaaDirectoryUrl":"https://web3.ncaa.org/directory/orgDetail?id=1","mensBasketballDivision":"II"}])
        self.assertEqual(result["counts"]["discrepancy"], 1)
if __name__ == "__main__":
    unittest.main()

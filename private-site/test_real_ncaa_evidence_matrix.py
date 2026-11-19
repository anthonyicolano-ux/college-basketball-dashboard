"""Verify real NCAA evidence files against the 365-school candidate matrix offline."""
import json
import unittest
from pathlib import Path
from reconcile_ncaa_sponsorship import reconcile

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "references/2026_27_mbb_school_evidence_matrix.json"
EVIDENCE = ROOT / "references/2026_27_mbb_ncaa_sport_evidence.json"

class RealEvidenceReconciliationTests(unittest.TestCase):
    def test_documented_sponsorship_and_pending_count(self):
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        self.assertEqual(len(matrix["schoolEvidence"]), 365)
        self.assertEqual(len(evidence), 5)
        result = reconcile(matrix, evidence)
        self.assertEqual(result["counts"].get("confirmed"), 5)
        self.assertEqual(result["counts"].get("pending"), 360)
        self.assertEqual(result["counts"].get("discrepancy", 0), 0)
        self.assertFalse(result["reviewed"])
        self.assertFalse(result["releaseApproved"])
        for record in evidence:
            self.assertEqual(record["mensBasketballDivision"], "I")
            self.assertTrue(record["ncaaDirectoryUrl"].startswith("https://web3.ncaa.org/directory/orgDetail?id="))

if __name__ == "__main__":
    unittest.main()

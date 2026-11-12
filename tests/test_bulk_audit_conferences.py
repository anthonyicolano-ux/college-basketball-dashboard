"""Regression checks for provider conference abbreviations and safe fuzzy diagnostics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_bulk_candidate_matching import same_conference, key, reconcile


class BulkAuditConferenceTests(unittest.TestCase):
    def test_known_provider_abbreviations(self):
        self.assertTrue(same_conference("America East", "Am. East"))
        self.assertTrue(same_conference("Missouri Valley", "MVC"))
        self.assertTrue(same_conference("America East", "America East Conference"))
        self.assertTrue(same_conference("Missouri Valley", "Missouri Valley Conference"))

    def test_unrelated_conferences_not_equivalent(self):
        self.assertFalse(same_conference("America East", "MVC"))
        self.assertFalse(same_conference("Missouri Valley", "Am. East"))
        self.assertFalse(same_conference("Metro", "MAAC"))

    def test_fuzzy_diagnostics_never_match(self):
        records = [{"season": 2027, "team": "Example Statee", "conference": "MVC"}]
        candidates = [{"name": "Example State", "conference": "Missouri Valley", "aliases": []}]
        report = reconcile(records, [], candidates)
        self.assertEqual(report["counts"]["unmatched_candidates"], 1)
        self.assertEqual(report["counts"]["unmatched_provider_records"], 1)
        self.assertEqual(report["counts"]["matched_unique_entries"], 0)
        self.assertEqual(report["publication"], "DISABLED")


if __name__ == "__main__":
    unittest.main()

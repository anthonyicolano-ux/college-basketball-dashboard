"""Offline regression tests for official 2026-27 membership review gates."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from finalize_official_membership_review import finalize

def rows():
    return [{"schoolName":f"School {i}",
             "official2026_27MbbEvidence":f"https://web3.ncaa.org/directory/memberDetail?institution={i}",
             "eligible2026_27":"yes"} for i in range(365)]

class OfficialReviewTests(unittest.TestCase):
    def test_reviewed_roster(self):
        result=finalize(rows())
        self.assertEqual(len(result["schoolNames"]),365)
        self.assertTrue(result["reviewed"])
        self.assertEqual(result["sport"],"mens_basketball")
    def test_unreviewed_row_rejected(self):
        data=rows();data[2]["eligible2026_27"]=""
        with self.assertRaises(ValueError):finalize(data)
    def test_unofficial_source_rejected(self):
        data=rows();data[2]["official2026_27MbbEvidence"]="https://example.com/directory"
        with self.assertRaises(ValueError):finalize(data)
    def test_malformed_source_rejected(self):
        data=rows();data[2]["official2026_27MbbEvidence"]="not a URL"
        with self.assertRaises(ValueError):finalize(data)
    def test_duplicate_school_rejected(self):
        data=rows();data[2]["schoolName"]="School 1"
        with self.assertRaises(ValueError):finalize(data)
    def test_missing_school_rejected(self):
        data=rows();data[2]["schoolName"]=""
        with self.assertRaises(ValueError):finalize(data)
    def test_no_reviewed_count_rejected(self):
        data=rows()
        for row in data[:70]:row["eligible2026_27"]="no"
        with self.assertRaises(ValueError):finalize(data)
    def test_explicit_no_excluded(self):
        data=rows();data[2]["eligible2026_27"]="no"
        result=finalize(data)
        self.assertEqual(len(result["schoolNames"]),364)
        self.assertNotIn("School 2",result["schoolNames"])

if __name__=="__main__":unittest.main()

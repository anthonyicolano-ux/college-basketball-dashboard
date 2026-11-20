"""Offline checks for provisional school staging; never imply NCAA approval."""
import unittest
from build_provisional_staging_manifest import build

def fixture():
    return {"season": 2027, "reviewed": False,
            "schoolEvidence": [
                {"schoolName": f"Candidate {i}", "conference": "Example",
                 "conferenceAffiliation": "checked", "ncaaSportSponsorship": "pending"}
                for i in range(365)]}

class ProvisionalStagingTests(unittest.TestCase):
    def test_candidate_manifest_remains_unapproved(self):
        rows = build(fixture())
        self.assertEqual(len(rows), 365)
        self.assertTrue(all(r["ncaaSportSponsorship"] == "pending" for r in rows))
        self.assertTrue(all(not r["ncaaSportSource"] for r in rows))

    def test_duplicate_school_rejected(self):
        payload = fixture()
        payload["schoolEvidence"][1]["schoolName"] = "Candidate 0"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build(payload)

    def test_approved_input_rejected(self):
        payload = fixture()
        payload["reviewed"] = True
        with self.assertRaisesRegex(ValueError, "unapproved"):
            build(payload)

    def test_unchecked_conference_rejected(self):
        payload = fixture()
        payload["schoolEvidence"][0]["conferenceAffiliation"] = "pending"
        with self.assertRaisesRegex(ValueError, "Unreconciled"):
            build(payload)

if __name__ == "__main__":
    unittest.main()

"""Offline safeguards for privately retained team IDs and reviewed membership."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from resolve_reviewed_membership_from_kv import resolve

MAP = {"season":2027,"reviewed":False,
       "status":"candidate_identity_only_not_division_one_approved",
       "teamIdsByName":{f"School {i}":i for i in range(365)}}
REVIEW = {"season":2027,"reviewed":True,"sport":"mens_basketball",
          "schoolNames":[f"School {i}" for i in range(365)]}

class MembershipResolutionTests(unittest.TestCase):
    def test_full_mapping(self):
        result=resolve(MAP,REVIEW)
        self.assertEqual(len(result["teamIds"]),365)
        self.assertTrue(result["reviewed"])
    def test_unreviewed_rejected(self):
        with self.assertRaises(ValueError):
            resolve(MAP,{**REVIEW,"reviewed":False})
    def test_missing_school_rejected(self):
        with self.assertRaises(ValueError):
            resolve(MAP,{**REVIEW,"schoolNames":REVIEW["schoolNames"][:-1]+["Missing"]})
    def test_duplicate_provider_id_rejected(self):
        mapping={**MAP,"teamIdsByName":{**MAP["teamIdsByName"],"School 1":0}}
        with self.assertRaises(ValueError):
            resolve(mapping,REVIEW)
    def test_candidate_map_cannot_claim_reviewed(self):
        with self.assertRaises(ValueError):
            resolve({**MAP,"reviewed":True},REVIEW)
    def test_wrong_sport_rejected(self):
        with self.assertRaises(ValueError):
            resolve(MAP,{**REVIEW,"sport":"football"})
    def test_duplicate_school_rejected(self):
        with self.assertRaises(ValueError):
            resolve(MAP,{**REVIEW,"schoolNames":REVIEW["schoolNames"][:-1]+["School 0"]})

if __name__ == "__main__":
    unittest.main()

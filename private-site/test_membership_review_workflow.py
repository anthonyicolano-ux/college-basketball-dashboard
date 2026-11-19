import unittest
from create_membership_review import draft
from finalize_membership_review import approved_membership


class MembershipReviewWorkflowTests(unittest.TestCase):
    def test_draft_is_unapproved_and_sorted(self):
        rows = draft([
            {"teamId": 2, "team": "Zulu", "conference": "A"},
            {"teamId": 1, "team": "Alpha", "conference": "B"},
        ])
        self.assertEqual([row["team"] for row in rows], ["Alpha", "Zulu"])
        self.assertTrue(all(row["divisionOneReview"] == "" for row in rows))

    def test_duplicate_provider_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            draft([{"teamId": 1, "team": "A"}, {"teamId": "1", "team": "B"}])

    def test_ambiguous_review_rejected(self):
        rows = [{"teamId": i, "divisionOneReview": "yes"} for i in range(300)]
        rows[5]["divisionOneReview"] = ""
        with self.assertRaisesRegex(ValueError, "Unreviewed"):
            approved_membership(rows)

    def test_approved_membership_requires_full_review(self):
        rows = [{"teamId": i, "divisionOneReview": "yes"} for i in range(300)]
        rows.append({"teamId": 300, "divisionOneReview": "no"})
        approved = approved_membership(rows)
        self.assertEqual(approved["season"], 2027)
        self.assertTrue(approved["reviewed"])
        self.assertEqual(len(approved["teamIds"]), 300)

    def test_duplicate_review_ids_rejected(self):
        rows = [{"teamId": i, "divisionOneReview": "yes"} for i in range(300)]
        rows.append({"teamId": "1", "divisionOneReview": "no"})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            approved_membership(rows)

    def test_too_few_approved_teams_rejected(self):
        rows = [{"teamId": i, "divisionOneReview": "yes"} for i in range(299)]
        with self.assertRaisesRegex(ValueError, "outside"):
            approved_membership(rows)


if __name__ == "__main__":
    unittest.main()

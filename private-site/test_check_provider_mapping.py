import unittest
from check_provider_mapping import summarize


class MappingReportTests(unittest.TestCase):
    def test_only_field_names_and_counts(self):
        report = summarize([{"team": "Secret School", "games": 3}], ("team", "games", "wins"))
        self.assertEqual(report["recordCount"], 1)
        self.assertEqual(report["missingRequiredFields"], {"wins": 1})
        self.assertNotIn("Secret School", str(report))

    def test_detects_missing_field_in_later_record(self):
        report = summarize([{"team": "A", "games": 3}, {"team": "B"}], ("team", "games"))
        self.assertEqual(report["missingRequiredFields"]["games"], 1)
        self.assertFalse(report["mappingReady"])

    def test_rejects_invalid_data(self):
        for rows in ([], {}, [None]):
            with self.assertRaises(ValueError):
                summarize(rows, ("team",))


if __name__ == "__main__":
    unittest.main()

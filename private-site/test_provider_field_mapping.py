import unittest
from provider_field_mapping import extract, map_records


class ProviderFieldMappingTests(unittest.TestCase):
    def test_nested_values(self):
        rows = [{"team": "Synthetic", "team_stats": {"points": 80},
                 "opponent_stats": {"points": 65}}]
        fields = {"team": "team", "ppg": "team_stats.points",
                  "oppPpg": "opponent_stats.points"}
        result = map_records(rows, fields, ("team", "ppg", "oppPpg"))
        self.assertEqual(result, [{"team": "Synthetic", "ppg": 80, "oppPpg": 65}])

    def test_missing_nested_field_fails(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            extract({"team_stats": {}}, "team_stats.points")

    def test_null_value_fails(self):
        with self.assertRaisesRegex(ValueError, "null"):
            extract({"stats": {"points": None}}, "stats.points")

    def test_missing_mapping_fails(self):
        with self.assertRaisesRegex(ValueError, "Unmapped"):
            map_records([{"team": "Synthetic"}], {"team": "team"}, ("team", "ppg"))

    def test_no_implicit_zero(self):
        with self.assertRaises(ValueError):
            map_records([{"stats": {}}], {"points": "stats.points"}, ("points",))


if __name__ == "__main__":
    unittest.main()

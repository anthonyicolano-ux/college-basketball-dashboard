import unittest
from inspect_provider_paths import flatten_paths, inventory


class ProviderPathsTests(unittest.TestCase):
    def test_nested_field_coverage_without_values(self):
        report=inventory([{"team":{"name":"Synthetic"},"stats":{"points":80}},
                          {"team":{"name":"Other"},"stats":{}}])
        self.assertEqual(report["recordCount"],2)
        fields={entry["path"]:entry for entry in report["paths"]}
        self.assertEqual(fields["stats.points"]["missing"],1)
        self.assertEqual(fields["team.name"]["present"],2)
        self.assertNotIn("Synthetic",str(report))
        self.assertNotIn("Other",str(report))

    def test_invalid_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            inventory([])
        with self.assertRaises(ValueError):
            inventory([{"team":"A"},None])


if __name__=="__main__":
    unittest.main()

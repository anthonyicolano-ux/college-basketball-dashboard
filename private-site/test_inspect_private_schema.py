"""Tests that schema inspection never prints private row values."""
import json
import tempfile
import unittest
from pathlib import Path
from inspect_private_schema import summarize


class SchemaInspectionTests(unittest.TestCase):
    def test_only_schema_metadata_returned(self):
        marker = "PRIVATE_PLAYER_MARKER_NOT_FOR_OUTPUT"
        dataset = {
            "schemaVersion": 1, "season": 2027, "demo": False,
            "approvedForPrivateDisplay": True, "source": "test fixture",
            "scope": "test", "generatedAt": "2026-11-18T00:00:00Z",
            "rows": [{"name": marker, "team": "Test Team", "games": 3,
                      "points": 42, "providerId": "PRIVATE_ID_MARKER"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps(dataset), encoding="utf-8")
            summary = summarize(path)
        serialized = json.dumps(summary)
        self.assertEqual(summary["rowCount"], 1)
        self.assertIn("name", summary["fields"])
        self.assertIn("providerId", summary["fields"])
        self.assertEqual(summary["missingRequiredFields"], ["assists", "minutes", "rebounds"])
        self.assertFalse(summary["requiredNumericTypesValid"])
        self.assertNotIn(marker, serialized)
        self.assertNotIn("PRIVATE_ID_MARKER", serialized)
        self.assertNotIn("Test Team", serialized)
        self.assertNotIn("test fixture", serialized)

    def test_empty_rows_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.json"
            path.write_text(json.dumps({"rows": []}), encoding="utf-8")
            summary = summarize(path)
        self.assertEqual(summary["rowCount"], 0)
        self.assertEqual(summary["fields"], [])
        self.assertFalse(summary["requiredNumericTypesValid"])
        self.assertTrue(summary["missingRequiredFields"])


if __name__ == "__main__":
    unittest.main()

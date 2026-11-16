"""No-network unit tests for aggregate game schema inventory."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_game_schema_inventory import inspect


class GameSchemaInventoryTests(unittest.TestCase):
    def test_aggregate_types_only(self):
        result = inspect([
            {"id": 1, "completed": True, "homePoints": 70, "comment": "fixture-text"},
            {"id": 2, "completed": False, "homePoints": None},
        ])
        self.assertEqual(result["records_returned"], 2)
        self.assertEqual(result["field_types"]["homePoints"], {"int": 1, "null": 1})
        self.assertNotIn("fixture-text", str(result))
        self.assertEqual(result["status"], "SCHEMA_INVENTORY_ONLY_COMPLETION_NOT_VERIFIED")

    def test_rejects_nonlist(self):
        with self.assertRaises(ValueError):
            inspect({"id": 1})

    def test_rejects_bad_rows(self):
        with self.assertRaises(ValueError):
            inspect([None])


if __name__ == "__main__":
    unittest.main()

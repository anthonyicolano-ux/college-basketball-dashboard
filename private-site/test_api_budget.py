"""Synthetic tests only: no provider calls and no credentials."""
import unittest
from api_budget import Budget, permit_refresh


class BudgetTests(unittest.TestCase):
    def test_sufficient_shared_balance(self):
        self.assertTrue(permit_refresh(Budget(remaining_calls=800, planned_calls=4)))

    def test_protects_football_and_safety_reserves(self):
        self.assertFalse(permit_refresh(Budget(remaining_calls=603, planned_calls=4)))

    def test_rejects_chatty_refresh(self):
        self.assertFalse(permit_refresh(Budget(remaining_calls=1000, planned_calls=100)))

    def test_rejects_unknown_or_invalid_balance(self):
        self.assertFalse(permit_refresh(Budget(remaining_calls=-1, planned_calls=4)))
        self.assertFalse(permit_refresh(Budget(remaining_calls=True, planned_calls=4)))
        self.assertFalse(permit_refresh(Budget(remaining_calls=900, planned_calls=0)))


if __name__ == "__main__":
    unittest.main()

"""Offline tests for the opt-in season snapshot fetcher."""
import unittest
from unittest.mock import patch
from fetch_season_snapshot import plan, fetch_json


class SnapshotTests(unittest.TestCase):
    def test_two_calls_for_season(self):
        urls = plan(800)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls, (\n            "https://api.collegebasketballdata.com/stats/team/season?season=2027",\n            "https://api.collegebasketballdata.com/stats/player/season?season=2027",\n        ))

    def test_budget_blocks_fetch(self):
        with self.assertRaises(ValueError):
            plan(601)

    def test_no_provider_calls_in_budget_tests(self):
        with patch("fetch_season_snapshot.urlopen") as opened:
            with self.assertRaises(ValueError):
                plan(0)
            opened.assert_not_called()

    def test_invalid_response_rejected(self):
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, _limit):
                return b'{"not":"an array"}'
        with patch("fetch_season_snapshot.urlopen", return_value=FakeResponse()):
            with self.assertRaises(ValueError):
                fetch_json("https://api.collegebasketballdata.com/stats/team/season?season=2027", "synthetic-token")


if __name__ == "__main__":
    unittest.main()

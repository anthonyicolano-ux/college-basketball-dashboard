"""Offline tests for the opt-in season snapshot fetcher."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from fetch_season_snapshot import plan, fetch_json, main


class SnapshotTests(unittest.TestCase):
    def test_two_calls_for_season(self):
        urls = plan(800)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls, (
            "https://api.collegebasketballdata.com/stats/team/season?season=2027",
            "https://api.collegebasketballdata.com/stats/player/season?season=2027",
        ))

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


    def test_empty_team_snapshot_skips_player_call(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch("fetch_season_snapshot.plan", return_value=("team-url", "player-url")), \
             patch("fetch_season_snapshot.fetch_json", return_value=[]) as fetch, \
             patch("fetch_season_snapshot.os.environ.get", return_value="synthetic-token"), \
             patch("fetch_season_snapshot.argparse.ArgumentParser.parse_args") as args:
            args.return_value.allow_network = True
            args.return_value.remaining_calls = 800
            args.return_value.out = Path(temp) / "raw"
            with self.assertRaisesRegex(ValueError, "player request skipped"):
                main()
            fetch.assert_called_once_with("team-url", "synthetic-token")
            self.assertEqual(list((Path(temp) / "raw").iterdir()), [])

    def test_small_team_snapshot_skips_player_call(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch("fetch_season_snapshot.plan", return_value=("team-url", "player-url")), \
             patch("fetch_season_snapshot.fetch_json", return_value=[{"team": f"Synthetic {i}"} for i in range(299)]) as fetch, \
             patch("fetch_season_snapshot.os.environ.get", return_value="synthetic-token"), \
             patch("fetch_season_snapshot.argparse.ArgumentParser.parse_args") as args:
            args.return_value.allow_network = True
            args.return_value.remaining_calls = 800
            args.return_value.out = Path(temp) / "raw"
            with self.assertRaisesRegex(ValueError, "Fewer than 300"):
                main()
            fetch.assert_called_once_with("team-url", "synthetic-token")
            self.assertEqual(list((Path(temp) / "raw").iterdir()), [])

    def test_empty_player_snapshot_saves_nothing(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch("fetch_season_snapshot.plan", return_value=("team-url", "player-url")), \
             patch("fetch_season_snapshot.fetch_json", side_effect=[[{"team": "Synthetic"}], []]) as fetch, \
             patch("fetch_season_snapshot.os.environ.get", return_value="synthetic-token"), \
             patch("fetch_season_snapshot.argparse.ArgumentParser.parse_args") as args:
            args.return_value.allow_network = True
            args.return_value.remaining_calls = 800
            args.return_value.out = Path(temp) / "raw"
            with self.assertRaisesRegex(ValueError, "nothing saved"):
                main()
            self.assertEqual(fetch.call_count, 2)
            self.assertEqual(list((Path(temp) / "raw").iterdir()), [])

if __name__ == "__main__":
    unittest.main()

"""Offline tests for privacy-limited CBBD game format summaries."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from probe_api import game_format_summary

class GameFormatTests(unittest.TestCase):
    def test_status_and_timestamp_shapes_only(self):
        records = [
            {'status': 'scheduled', 'startDate': '2026-11-15T19:30:00-06:00', 'startTimeTbd': False},
            {'status': 'scheduled', 'startDate': '2026-11-16T01:30:00Z', 'startTimeTbd': True},
            {'status': 'final', 'startDate': '2026-11-17', 'startTimeTbd': False},
            {'status': 'canceled', 'startDate': '2026-11-18T12:00:00', 'startTimeTbd': None},
        ]
        result = game_format_summary(records)
        self.assertEqual(result['status_counts']['scheduled'], 2)
        self.assertEqual(result['start_date_formats'],
                         {'date-only': 1, 'offset-aware': 1, 'timezone-missing': 1, 'utc-Z': 1})
        self.assertEqual(result['start_time_tbd_counts'],
                         {'false': 2, 'missing-or-invalid': 1, 'true': 1})
        self.assertNotIn('2026-11', str(result))

    def test_arbitrary_status_not_echoed(self):
        result = game_format_summary([{'status': 'private@example.com', 'startDate': 'not-a-date'}])
        self.assertEqual(result['status_counts'], {'<missing-or-unexpected>': 1})
        self.assertEqual(result['start_date_formats'], {'unrecognized': 1})

    def test_empty_and_invalid_input(self):
        self.assertEqual(game_format_summary([])['status_counts'], {})
        self.assertIn('error', game_format_summary({}))

if __name__ == '__main__':
    unittest.main()
